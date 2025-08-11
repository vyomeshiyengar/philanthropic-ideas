"""
Base data ingester class for the Philanthropic Ideas Generator.
"""
import asyncio
import aiohttp
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Generator
from datetime import datetime, timedelta
from dataclasses import dataclass
from ratelimit import limits, sleep_and_retry

from config.settings import settings
from storage.database import db_manager
from storage.models import DataSource, RawData, SearchQuery
from storage.cache import api_cache

logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
    """Result of a data ingestion operation."""
    success: bool
    items_processed: int
    items_successful: int
    items_failed: int
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseDataIngester(ABC):
    """Base class for all data ingesters."""
    
    def __init__(self, source_name: str, source_config: Dict[str, Any]):
        self.source_name = source_name
        self.source_config = source_config
        self.base_url = source_config.get("base_url", "")
        self.rate_limit = source_config.get("rate_limit", 100)
        self.session = None
        self.data_source_id = None
        
        # Initialize data source in database
        self._init_data_source()
    
    def _init_data_source(self):
        """Initialize or get the data source record in the database."""
        with db_manager.get_session() as session:
            data_source = session.query(DataSource).filter(
                DataSource.name == self.source_name
            ).first()
            
            if not data_source:
                data_source = DataSource(
                    name=self.source_name,
                    source_type="api",
                    url=self.base_url,
                    api_key_required=bool(self.source_config.get("api_key")),
                    rate_limit=self.rate_limit,
                    status="active"
                )
                session.add(data_source)
                session.commit()
                session.refresh(data_source)
            
            self.data_source_id = data_source.id
            logger.info(f"Initialized data source: {self.source_name} (ID: {self.data_source_id})")
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers=self._get_headers()
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {
            "User-Agent": "PhilanthropicIdeasGenerator/1.0",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Add API key if available
        api_key = self.source_config.get("api_key")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        return headers
    
    @sleep_and_retry
    @limits(calls=100, period=3600)  # 100 calls per hour default
    async def _make_request(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make a rate-limited API request with caching."""
        # Check cache first
        cached_response = api_cache.get(self.source_name, url, params)
        
        if cached_response is not None:
            logger.debug(f"Cache hit for {self.source_name}:{url}")
            return cached_response.get("data")
        
        # Make actual API request
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Cache the response
                    api_cache.set(self.source_name, url, {"data": data}, params)
                    logger.debug(f"Cached response for {self.source_name}:{url}")
                    
                    return data
                elif response.status == 429:  # Rate limited
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    return await self._make_request(url, params)
                else:
                    logger.error(f"API request failed: {response.status} - {response.reason}")
                    return None
        except Exception as e:
            logger.error(f"Request error: {e}")
            return None
    
    def _log_search_query(self, query: str, domain: Optional[str] = None, 
                         results_count: int = 0, successful: bool = True,
                         error_message: Optional[str] = None) -> None:
        """Log a search query to the database."""
        try:
            with db_manager.get_session() as session:
                search_query = SearchQuery(
                    query_text=query,
                    data_source=self.source_name,
                    domain=domain,
                    results_count=results_count,
                    successful=successful,
                    error_message=error_message
                )
                session.add(search_query)
                session.commit()
        except Exception as e:
            logger.error(f"Failed to log search query: {e}")
    
    def _save_raw_data(self, content_type: str, title: Optional[str] = None,
                      authors: Optional[List[str]] = None, abstract: Optional[str] = None,
                      full_text: Optional[str] = None, url: Optional[str] = None,
                      publication_date: Optional[datetime] = None,
                      keywords: Optional[List[str]] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """Save raw data to the database."""
        try:
            with db_manager.get_session() as session:
                raw_data = RawData(
                    data_source_id=self.data_source_id,
                    content_type=content_type,
                    title=title,
                    authors=authors,
                    abstract=abstract,
                    full_text=full_text,
                    url=url,
                    publication_date=publication_date,
                    keywords=keywords,
                    metadata_json=metadata
                )
                session.add(raw_data)
                session.commit()
                session.refresh(raw_data)
                return raw_data.id
        except Exception as e:
            logger.error(f"Failed to save raw data: {e}")
            return None
    
    @abstractmethod
    async def search(self, query: str, domain: Optional[str] = None, 
                    max_results: int = 100) -> IngestionResult:
        """Search for data using the specific API."""
        pass
    
    @abstractmethod
    async def fetch_details(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed information for a specific item."""
        pass
    
    async def ingest_domain_data(self, domain: str, keywords: List[str], 
                                max_results_per_keyword: int = 50) -> IngestionResult:
        """Ingest data for a specific domain using multiple keywords."""
        total_processed = 0
        total_successful = 0
        total_failed = 0
        errors = []
        
        logger.info(f"Starting ingestion for domain: {domain}")
        
        for keyword in keywords:
            try:
                logger.info(f"Searching for keyword: {keyword}")
                result = await self.search(
                    query=keyword,
                    domain=domain,
                    max_results=max_results_per_keyword
                )
                
                total_processed += result.items_processed
                total_successful += result.items_successful
                total_failed += result.items_failed
                
                if result.error_message:
                    errors.append(f"{keyword}: {result.error_message}")
                
                # Rate limiting between searches
                await asyncio.sleep(1)
                
            except Exception as e:
                error_msg = f"Failed to process keyword '{keyword}': {e}"
                logger.error(error_msg)
                errors.append(error_msg)
                total_failed += 1
        
        return IngestionResult(
            success=total_failed == 0,
            items_processed=total_processed,
            items_successful=total_successful,
            items_failed=total_failed,
            error_message="; ".join(errors) if errors else None,
            metadata={"domain": domain, "keywords_processed": len(keywords)}
        )
    
    def update_data_source_status(self, status: str, error_message: Optional[str] = None):
        """Update the data source status in the database."""
        try:
            with db_manager.get_session() as session:
                data_source = session.query(DataSource).filter(
                    DataSource.id == self.data_source_id
                ).first()
                
                if data_source:
                    data_source.status = status
                    data_source.last_accessed = datetime.now()
                    if error_message:
                                            data_source.metadata_json = data_source.metadata_json or {}
                    data_source.metadata_json["last_error"] = error_message
                    
                    session.commit()
                    logger.info(f"Updated data source status: {self.source_name} -> {status}")
        except Exception as e:
            logger.error(f"Failed to update data source status: {e}")


class WebScraperIngester(BaseDataIngester):
    """Base class for web scraping ingesters."""
    
    def __init__(self, source_name: str, source_config: Dict[str, Any]):
        super().__init__(source_name, source_config)
        self.base_url = source_config.get("base_url", "")
    
    async def scrape_page(self, url: str) -> Optional[str]:
        """Scrape content from a web page."""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.error(f"Failed to scrape {url}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Scraping error for {url}: {e}")
            return None
    
    @abstractmethod
    def parse_content(self, html_content: str) -> List[Dict[str, Any]]:
        """Parse HTML content to extract structured data."""
        pass
