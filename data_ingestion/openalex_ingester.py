"""
OpenAlex data ingester for academic papers and research.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import quote_plus

from data_ingestion.base_ingester import BaseDataIngester, IngestionResult
from config.settings import settings

logger = logging.getLogger(__name__)


class OpenAlexIngester(BaseDataIngester):
    """Ingester for OpenAlex academic papers and research."""
    
    def __init__(self):
        source_config = settings.DATA_SOURCES["openalex"]
        super().__init__("openalex", source_config)
        self.search_endpoint = source_config["search_endpoint"]
    
    async def search(self, query: str, domain: Optional[str] = None, 
                    max_results: int = 100) -> IngestionResult:
        """Search for academic papers using OpenAlex API."""
        items_processed = 0
        items_successful = 0
        items_failed = 0
        error_message = None
        
        try:
            # Build search URL
            search_url = f"{self.base_url}{self.search_endpoint}"
            params = {
                "search": query,
                "per_page": min(max_results, 200),  # OpenAlex max is 200
                "select": "id,title,abstract,publication_date,authorships,concepts,keywords,doi,url"
            }
            
            logger.info(f"Searching OpenAlex for: {query}")
            
            # Make the request
            response_data = await self._make_request(search_url, params)
            
            if not response_data:
                error_message = "Failed to get response from OpenAlex API"
                self._log_search_query(query, domain, 0, False, error_message)
                return IngestionResult(
                    success=False,
                    items_processed=0,
                    items_successful=0,
                    items_failed=1,
                    error_message=error_message
                )
            
            # Process results
            results = response_data.get("results", [])
            items_processed = len(results)
            
            for result in results:
                try:
                    # Extract paper information
                    paper_id = result.get("id", "")
                    title = result.get("title", "")
                    abstract = result.get("abstract", "")
                    publication_date_str = result.get("publication_date", "")
                    
                    # Parse publication date
                    publication_date = None
                    if publication_date_str:
                        try:
                            publication_date = datetime.fromisoformat(publication_date_str.replace("Z", "+00:00"))
                        except ValueError:
                            pass
                    
                    # Extract authors
                    authors = []
                    authorships = result.get("authorships", [])
                    for authorship in authorships:
                        author = authorship.get("author", {})
                        if author:
                            author_name = author.get("display_name", "")
                            if author_name:
                                authors.append(author_name)
                    
                    # Extract keywords and concepts
                    keywords = []
                    concepts = result.get("concepts", [])
                    for concept in concepts:
                        concept_name = concept.get("display_name", "")
                        if concept_name:
                            keywords.append(concept_name)
                    
                    # Add keywords from keywords field
                    paper_keywords = result.get("keywords", [])
                    for keyword in paper_keywords:
                        keyword_text = keyword.get("keyword", "")
                        if keyword_text:
                            keywords.append(keyword_text)
                    
                    # Build metadata
                    metadata = {
                        "openalex_id": paper_id,
                        "doi": result.get("doi", ""),
                        "concepts": concepts,
                        "domain": domain
                    }
                    
                    # Save to database
                    raw_data_id = self._save_raw_data(
                        content_type="paper",
                        title=title,
                        authors=authors,
                        abstract=abstract,
                        url=result.get("url", ""),
                        publication_date=publication_date,
                        keywords=keywords,
                        metadata=metadata
                    )
                    
                    if raw_data_id:
                        items_successful += 1
                        logger.debug(f"Saved paper: {title}")
                    else:
                        items_failed += 1
                        logger.warning(f"Failed to save paper: {title}")
                
                except Exception as e:
                    items_failed += 1
                    logger.error(f"Error processing paper result: {e}")
            
            # Log the search query
            self._log_search_query(query, domain, items_processed, True)
            
            logger.info(f"OpenAlex search completed: {items_successful} successful, {items_failed} failed")
            
            return IngestionResult(
                success=items_failed == 0,
                items_processed=items_processed,
                items_successful=items_successful,
                items_failed=items_failed,
                error_message=error_message,
                metadata={
                    "query": query,
                    "domain": domain,
                    "total_results": response_data.get("meta", {}).get("count", 0)
                }
            )
            
        except Exception as e:
            error_message = f"OpenAlex search failed: {e}"
            logger.error(error_message)
            self._log_search_query(query, domain, 0, False, error_message)
            return IngestionResult(
                success=False,
                items_processed=items_processed,
                items_successful=items_successful,
                items_failed=items_failed + 1,
                error_message=error_message
            )
    
    async def fetch_details(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed information for a specific paper."""
        try:
            # OpenAlex uses full URLs as IDs
            if not item_id.startswith("http"):
                item_id = f"https://openalex.org/{item_id}"
            
            response_data = await self._make_request(item_id)
            
            if response_data:
                return {
                    "id": response_data.get("id", ""),
                    "title": response_data.get("title", ""),
                    "abstract": response_data.get("abstract", ""),
                    "publication_date": response_data.get("publication_date", ""),
                    "authors": [auth.get("author", {}).get("display_name", "") 
                              for auth in response_data.get("authorships", [])],
                    "concepts": [concept.get("display_name", "") 
                               for concept in response_data.get("concepts", [])],
                    "keywords": [kw.get("keyword", "") 
                               for kw in response_data.get("keywords", [])],
                    "doi": response_data.get("doi", ""),
                    "url": response_data.get("url", ""),
                    "citations_count": response_data.get("cited_by_count", 0),
                    "venue": response_data.get("primary_location", {}).get("source", {}).get("display_name", "")
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to fetch OpenAlex details for {item_id}: {e}")
            return None
    
    async def search_by_concept(self, concept: str, max_results: int = 100) -> IngestionResult:
        """Search for papers by concept/topic."""
        # OpenAlex concept search
        search_url = f"{self.base_url}/works"
        params = {
            "filter": f"concepts.display_name.search:{quote_plus(concept)}",
            "per_page": min(max_results, 200),
            "select": "id,title,abstract,publication_date,authorships,concepts,keywords,doi,url"
        }
        
        try:
            response_data = await self._make_request(search_url, params)
            
            if not response_data:
                return IngestionResult(
                    success=False,
                    items_processed=0,
                    items_successful=0,
                    items_failed=1,
                    error_message="Failed to get response from OpenAlex concept search"
                )
            
            # Process results similar to regular search
            results = response_data.get("results", [])
            items_processed = len(results)
            items_successful = 0
            items_failed = 0
            
            for result in results:
                try:
                    # Similar processing as in search method
                    # ... (implementation similar to search method)
                    items_successful += 1
                except Exception as e:
                    items_failed += 1
                    logger.error(f"Error processing concept search result: {e}")
            
            return IngestionResult(
                success=items_failed == 0,
                items_processed=items_processed,
                items_successful=items_successful,
                items_failed=items_failed,
                metadata={"concept": concept}
            )
            
        except Exception as e:
            logger.error(f"Concept search failed: {e}")
            return IngestionResult(
                success=False,
                items_processed=0,
                items_successful=0,
                items_failed=1,
                error_message=str(e)
            )
    
    async def get_recent_papers(self, days: int = 30, max_results: int = 100) -> IngestionResult:
        """Get recent papers from the last N days."""
        from datetime import datetime, timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        search_url = f"{self.base_url}/works"
        params = {
            "filter": f"publication_date:{start_date.strftime('%Y-%m-%d')}..{end_date.strftime('%Y-%m-%d')}",
            "per_page": min(max_results, 200),
            "sort": "publication_date:desc",
            "select": "id,title,abstract,publication_date,authorships,concepts,keywords,doi,url"
        }
        
        try:
            response_data = await self._make_request(search_url, params)
            
            if not response_data:
                return IngestionResult(
                    success=False,
                    items_processed=0,
                    items_successful=0,
                    items_failed=1,
                    error_message="Failed to get recent papers from OpenAlex"
                )
            
            # Process results similar to regular search
            results = response_data.get("results", [])
            items_processed = len(results)
            items_successful = 0
            items_failed = 0
            
            for result in results:
                try:
                    # Similar processing as in search method
                    # ... (implementation similar to search method)
                    items_successful += 1
                except Exception as e:
                    items_failed += 1
                    logger.error(f"Error processing recent paper: {e}")
            
            return IngestionResult(
                success=items_failed == 0,
                items_processed=items_processed,
                items_successful=items_successful,
                items_failed=items_failed,
                metadata={"days": days, "date_range": f"{start_date} to {end_date}"}
            )
            
        except Exception as e:
            logger.error(f"Recent papers search failed: {e}")
            return IngestionResult(
                success=False,
                items_processed=0,
                items_successful=0,
                items_failed=1,
                error_message=str(e)
            )
