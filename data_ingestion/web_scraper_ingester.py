import logging
import asyncio
import aiohttp
import feedparser
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
from dataclasses import dataclass

from data_ingestion.base_ingester import WebScraperIngester, IngestionResult
from config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class RSSFeedItem:
    title: str
    link: str
    description: str
    published: Optional[datetime]
    author: Optional[str]
    content: Optional[str]

class WebScraperIngester(WebScraperIngester):
    def __init__(self):
        super().__init__("web_scraper", {"base_url": "https://example.com", "enabled": True})
        self.session = None
        self.expert_sources = settings.EXPERT_SOURCES
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def search(self, query: str, domain: Optional[str] = None, max_results: int = 100) -> IngestionResult:
        """Search across all expert sources for content matching the query."""
        results = []
        total_processed = 0
        total_successful = 0
        total_failed = 0
        
        for source in self.expert_sources:
            if not source.get("enabled", True):
                continue
                
            try:
                source_results = await self._scrape_source(source, query, max_results)
                results.extend(source_results)
                total_processed += len(source_results)
                total_successful += len(source_results)
            except Exception as e:
                logger.error(f"Failed to scrape source {source['name']}: {e}")
                total_failed += 1
                
        return IngestionResult(
            source_name="web_scraper",
            items_processed=total_processed,
            items_successful=total_successful,
            items_failed=total_failed,
            raw_data=results
        )
        
    async def _scrape_source(self, source: Dict[str, Any], query: str, max_results: int) -> List[Dict[str, Any]]:
        """Scrape content from a specific source."""
        source_type = source.get("type", "rss")
        
        if source_type == "rss":
            return await self._scrape_rss_feed(source, query, max_results)
        elif source_type == "blog":
            return await self._scrape_blog(source, query, max_results)
        else:
            logger.warning(f"Unknown source type: {source_type}")
            return []
            
    async def _scrape_rss_feed(self, source: Dict[str, Any], query: str, max_results: int) -> List[Dict[str, Any]]:
        """Scrape content from RSS feeds."""
        rss_url = source.get("rss_url")
        if not rss_url:
            logger.warning(f"No RSS URL provided for source: {source['name']}")
            return []
            
        try:
            async with self.session.get(rss_url) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch RSS feed {rss_url}: {response.status}")
                    return []
                    
                content = await response.text()
                feed = feedparser.parse(content)
                
                items = []
                for entry in feed.entries[:max_results]:
                    # Check if entry matches query (basic keyword matching)
                    if self._matches_query(entry, query):
                        rss_item = RSSFeedItem(
                            title=entry.get("title", ""),
                            link=entry.get("link", ""),
                            description=entry.get("description", ""),
                            published=self._parse_date(entry.get("published")),
                            author=entry.get("author", ""),
                            content=entry.get("content", [{}])[0].get("value", "") if entry.get("content") else ""
                        )
                        
                        # Scrape full article content if available
                        full_content = await self._scrape_article_content(rss_item.link)
                        
                        items.append({
                            "source_name": source["name"],
                            "source_url": source.get("url", ""),
                            "title": rss_item.title,
                            "url": rss_item.link,
                            "description": rss_item.description,
                            "content": full_content or rss_item.content,
                            "author": rss_item.author,
                            "published_date": rss_item.published.isoformat() if rss_item.published else None,
                            "scraped_at": datetime.utcnow().isoformat(),
                            "content_type": "article"
                        })
                        
                return items
                
        except Exception as e:
            logger.error(f"Error scraping RSS feed {rss_url}: {e}")
            return []
            
    async def _scrape_blog(self, source: Dict[str, Any], query: str, max_results: int) -> List[Dict[str, Any]]:
        """Scrape content from blog websites."""
        blog_url = source.get("url")
        if not blog_url:
            logger.warning(f"No URL provided for blog source: {source['name']}")
            return []
            
        try:
            # Get the main page
            async with self.session.get(blog_url) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch blog {blog_url}: {response.status}")
                    return []
                    
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Extract article links (this is a generic approach)
                article_links = self._extract_article_links(soup, blog_url)
                
                items = []
                for link in article_links[:max_results]:
                    try:
                        article_content = await self._scrape_article_content(link)
                        if article_content and self._matches_query_text(article_content, query):
                            items.append({
                                "source_name": source["name"],
                                "source_url": blog_url,
                                "title": self._extract_title_from_url(link),
                                "url": link,
                                "description": article_content[:500] + "..." if len(article_content) > 500 else article_content,
                                "content": article_content,
                                "author": None,  # Would need to extract from article
                                "published_date": None,  # Would need to extract from article
                                "scraped_at": datetime.utcnow().isoformat(),
                                "content_type": "article"
                            })
                    except Exception as e:
                        logger.error(f"Error scraping article {link}: {e}")
                        continue
                        
                return items
                
        except Exception as e:
            logger.error(f"Error scraping blog {blog_url}: {e}")
            return []
            
    async def _scrape_article_content(self, url: str) -> Optional[str]:
        """Scrape the full content of an article."""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None
                    
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                    
                # Try to find the main content area
                content_selectors = [
                    'article',
                    '.post-content',
                    '.entry-content',
                    '.article-content',
                    '.content',
                    'main',
                    '.main-content'
                ]
                
                content_element = None
                for selector in content_selectors:
                    content_element = soup.select_one(selector)
                    if content_element:
                        break
                        
                if not content_element:
                    # Fallback to body content
                    content_element = soup.find('body')
                    
                if content_element:
                    # Extract text and clean it up
                    text = content_element.get_text()
                    # Clean up whitespace
                    text = re.sub(r'\s+', ' ', text).strip()
                    return text
                    
                return None
                
        except Exception as e:
            logger.error(f"Error scraping article content from {url}: {e}")
            return None
            
    def _matches_query(self, entry: Any, query: str) -> bool:
        """Check if an RSS entry matches the query."""
        if not query:
            return True
            
        query_terms = query.lower().split()
        text_to_search = f"{entry.get('title', '')} {entry.get('description', '')}".lower()
        
        return any(term in text_to_search for term in query_terms)
        
    def _matches_query_text(self, text: str, query: str) -> bool:
        """Check if text content matches the query."""
        if not query:
            return True
            
        query_terms = query.lower().split()
        text_lower = text.lower()
        
        return any(term in text_lower for term in query_terms)
        
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string into datetime object."""
        if not date_str:
            return None
            
        try:
            # Try common date formats
            formats = [
                '%a, %d %b %Y %H:%M:%S %z',
                '%a, %d %b %Y %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S%z',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
                    
            return None
        except Exception:
            return None
            
    def _extract_article_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract article links from a blog page."""
        links = []
        
        # Common selectors for article links
        link_selectors = [
            'a[href*="/post/"]',
            'a[href*="/article/"]',
            'a[href*="/blog/"]',
            'a[href*="/entry/"]',
            '.post-title a',
            '.entry-title a',
            'article a',
            '.article-link'
        ]
        
        for selector in link_selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if full_url not in links:
                        links.append(full_url)
                        
        return links
        
    def _extract_title_from_url(self, url: str) -> str:
        """Extract a title from URL path."""
        path = urlparse(url).path
        # Remove common path components and clean up
        title = path.strip('/').split('/')[-1]
        title = title.replace('-', ' ').replace('_', ' ')
        return title.title()
        
    async def scrape_all_sources(self, max_results_per_source: int = 50) -> IngestionResult:
        """Scrape all enabled expert sources."""
        all_results = []
        total_processed = 0
        total_successful = 0
        total_failed = 0
        
        for source in self.expert_sources:
            if not source.get("enabled", True):
                continue
                
            try:
                source_results = await self._scrape_source(source, "", max_results_per_source)
                all_results.extend(source_results)
                total_processed += len(source_results)
                total_successful += len(source_results)
                logger.info(f"Scraped {len(source_results)} items from {source['name']}")
            except Exception as e:
                logger.error(f"Failed to scrape source {source['name']}: {e}")
                total_failed += 1
                
        return IngestionResult(
            source_name="web_scraper",
            items_processed=total_processed,
            items_successful=total_successful,
            items_failed=total_failed,
            raw_data=all_results
        )
        
    async def scrape_recent_content(self, days: int = 30, max_results_per_source: int = 20) -> IngestionResult:
        """Scrape recent content from all sources."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        all_results = []
        total_processed = 0
        total_successful = 0
        total_failed = 0
        
        for source in self.expert_sources:
            if not source.get("enabled", True):
                continue
                
            try:
                source_results = await self._scrape_source(source, "", max_results_per_source)
                
                # Filter for recent content
                recent_results = []
                for result in source_results:
                    if result.get("published_date"):
                        try:
                            published_date = datetime.fromisoformat(result["published_date"].replace('Z', '+00:00'))
                            if published_date >= cutoff_date:
                                recent_results.append(result)
                        except Exception:
                            # If we can't parse the date, include it anyway
                            recent_results.append(result)
                    else:
                        # If no date, include it
                        recent_results.append(result)
                        
                all_results.extend(recent_results)
                total_processed += len(source_results)
                total_successful += len(recent_results)
                logger.info(f"Scraped {len(recent_results)} recent items from {source['name']}")
            except Exception as e:
                logger.error(f"Failed to scrape source {source['name']}: {e}")
                total_failed += 1
                
        return IngestionResult(
            source_name="web_scraper",
            items_processed=total_processed,
            items_successful=total_successful,
            items_failed=total_failed,
            raw_data=all_results
        )
