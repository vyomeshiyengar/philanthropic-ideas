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

from data_ingestion.base_ingester import BaseDataIngester, IngestionResult
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

class WebScraperIngester(BaseDataIngester):
    def __init__(self):
        super().__init__("web_scraper", {
            "base_url": "https://example.com", 
            "enabled": True,
            "requires_auth": False  # Web scraping doesn't require authentication
        })
        self.session = None
        self.expert_sources = settings.EXPERT_SOURCES
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
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
            success=total_failed == 0,
            items_processed=total_processed,
            items_successful=total_successful,
            items_failed=total_failed,
            metadata={"sources_scraped": len(self.expert_sources)}
        )
        
    async def _scrape_source(self, source: Dict[str, Any], query: str, max_results: int) -> List[Dict[str, Any]]:
        """Scrape content from a specific source."""
        source_type = source.get("type", "blog")  # Default to blog instead of rss
        
        # Special handling for Substack
        if source_type == "substack":
            return await self._scrape_substack(source, query, max_results)
        elif source_type in ["blog", "organization", "forum", "magazine", "publisher"]:
            return await self._scrape_blog(source, query, max_results)
        elif source_type == "rss":
            return await self._scrape_rss_feed(source, query, max_results)
        else:
            logger.warning(f"Unknown source type: {source_type}, treating as blog")
            return await self._scrape_blog(source, query, max_results)
            
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
            # Get the main page with timeout
            timeout = aiohttp.ClientTimeout(total=15, connect=5)
            async with self.session.get(blog_url, timeout=timeout) as response:
                if response.status != 200:
                    logger.debug(f"Failed to fetch blog {blog_url}: {response.status}")
                    return []
                    
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Extract article links (this is a generic approach)
                article_links = self._extract_article_links(soup, blog_url)
                
                # Limit the number of articles to process
                article_links = article_links[:min(max_results, 3)]  # Limit to 3 articles per source
                
                items = []
                for i, link in enumerate(article_links):
                    try:
                        # Add delay between requests to be respectful
                        if i > 0:
                            await asyncio.sleep(2)
                            
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
                    except asyncio.CancelledError:
                        logger.debug(f"Cancelled processing articles from {blog_url}")
                        break
                    except Exception as e:
                        logger.debug(f"Error scraping article {link}: {e}")
                        continue
                        
                return items
                
        except asyncio.TimeoutError:
            logger.debug(f"Timeout accessing blog {blog_url}")
            return []
        except asyncio.CancelledError:
            logger.debug(f"Cancelled scraping blog {blog_url}")
            return []
        except Exception as e:
            logger.debug(f"Error scraping blog {blog_url}: {e}")
            return []
            
    async def _scrape_substack(self, source: Dict[str, Any], query: str, max_results: int) -> List[Dict[str, Any]]:
        """Scrape content from Substack newsletters."""
        substack_url = source.get("url")
        if not substack_url:
            logger.warning(f"No URL provided for Substack source: {source['name']}")
            return []
            
        try:
            # Try multiple approaches for Substack
            items = []
            
            # Approach 1: Try RSS feed if available
            rss_url = f"{substack_url}/feed"
            try:
                rss_items = await self._scrape_rss_feed({"rss_url": rss_url, "name": source["name"]}, query, max_results)
                items.extend(rss_items)
                logger.info(f"Found {len(rss_items)} items via RSS for {source['name']}")
            except Exception as e:
                logger.debug(f"RSS approach failed for {source['name']}: {e}")
            
            # Approach 2: Try direct API access (Substack has a public API)
            if len(items) < max_results:
                try:
                    api_items = await self._scrape_substack_api(source, query, max_results - len(items))
                    items.extend(api_items)
                    logger.info(f"Found {len(api_items)} items via API for {source['name']}")
                except Exception as e:
                    logger.debug(f"API approach failed for {source['name']}: {e}")
            
            # Approach 3: Try archive page scraping
            if len(items) < max_results:
                try:
                    archive_items = await self._scrape_substack_archive(source, query, max_results - len(items))
                    items.extend(archive_items)
                    logger.info(f"Found {len(archive_items)} items via archive for {source['name']}")
                except Exception as e:
                    logger.debug(f"Archive approach failed for {source['name']}: {e}")
            
            return items[:max_results]
            
        except Exception as e:
            logger.error(f"Error scraping Substack {substack_url}: {e}")
            return []
            
    async def _scrape_substack_api(self, source: Dict[str, Any], query: str, max_results: int) -> List[Dict[str, Any]]:
        """Scrape content using Substack's public API."""
        substack_url = source.get("url")
        substack_name = source["name"].lower().replace(" ", "")
        
        try:
            # Substack API endpoint
            api_url = f"https://{substack_name}.substack.com/api/v1/publication/posts"
            
            timeout = aiohttp.ClientTimeout(total=15, connect=5)
            async with self.session.get(api_url, timeout=timeout) as response:
                if response.status == 200:
                    data = await response.json()
                    posts = data.get("posts", [])
                    
                    items = []
                    for post in posts[:max_results]:
                        if self._matches_query_text(post.get("title", "") + " " + post.get("subtitle", ""), query):
                            # Get full post content
                            post_url = f"{substack_url}/p/{post.get('slug', '')}"
                            content = await self._scrape_article_content(post_url)
                            
                            if content:
                                items.append({
                                    "source_name": source["name"],
                                    "source_url": substack_url,
                                    "title": post.get("title", "No title"),
                                    "url": post_url,
                                    "description": content[:500] + "..." if len(content) > 500 else content,
                                    "content": content,
                                    "author": post.get("author", {}).get("name"),
                                    "published_date": post.get("published_at"),
                                    "scraped_at": datetime.utcnow().isoformat(),
                                    "content_type": "article"
                                })
                    
                    return items
                else:
                    logger.debug(f"Substack API returned status {response.status}")
                    return []
                    
        except Exception as e:
            logger.debug(f"Substack API scraping failed: {e}")
            return []
            
    async def _scrape_substack_archive(self, source: Dict[str, Any], query: str, max_results: int) -> List[Dict[str, Any]]:
        """Scrape content from Substack archive page."""
        substack_url = source.get("url")
        archive_url = f"{substack_url}/archive"
        
        try:
            timeout = aiohttp.ClientTimeout(total=15, connect=5)
            async with self.session.get(archive_url, timeout=timeout) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Look for post links in archive
                    post_links = []
                    for link in soup.find_all('a', href=True):
                        href = link.get('href', '')
                        if '/p/' in href and href.startswith('/'):
                            full_url = f"{substack_url}{href}"
                            title = link.get_text(strip=True)
                            if title and self._matches_query_text(title, query):
                                post_links.append((full_url, title))
                    
                    # Get content from found posts
                    items = []
                    for url, title in post_links[:max_results]:
                        try:
                            content = await self._scrape_article_content(url)
                            if content:
                                items.append({
                                    "source_name": source["name"],
                                    "source_url": substack_url,
                                    "title": title,
                                    "url": url,
                                    "description": content[:500] + "..." if len(content) > 500 else content,
                                    "content": content,
                                    "author": None,
                                    "published_date": None,
                                    "scraped_at": datetime.utcnow().isoformat(),
                                    "content_type": "article"
                                })
                        except Exception as e:
                            logger.debug(f"Error scraping post {url}: {e}")
                            continue
                    
                    return items
                else:
                    logger.debug(f"Archive page returned status {response.status}")
                    return []
                    
        except Exception as e:
            logger.debug(f"Archive scraping failed: {e}")
            return []
            
    async def _scrape_article_content(self, url: str) -> Optional[str]:
        """Scrape the full content of an article."""
        try:
            # Add timeout and better error handling
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            async with self.session.get(url, timeout=timeout) as response:
                if response.status != 200:
                    logger.debug(f"Failed to scrape {url}: status {response.status}")
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
                    return text if len(text) > 100 else None  # Only return if substantial content
                    
                return None
                
        except asyncio.TimeoutError:
            logger.debug(f"Timeout scraping {url}")
            return None
        except asyncio.CancelledError:
            logger.debug(f"Cancelled scraping {url}")
            return None
        except Exception as e:
            logger.debug(f"Error scraping article content from {url}: {e}")
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
            success=total_failed == 0,
            items_processed=total_processed,
            items_successful=total_successful,
            items_failed=total_failed,
            metadata={"sources_scraped": len(self.expert_sources)}
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
            success=total_failed == 0,
            items_processed=total_processed,
            items_successful=total_successful,
            items_failed=total_failed,
            metadata={"days_back": days}
        )

    async def fetch_details(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed information for a specific web content item."""
        try:
            # For web scraper, item_id is typically a URL
            if not item_id.startswith(('http://', 'https://')):
                logger.warning(f"Invalid URL for web scraper: {item_id}")
                return None
            
            content = await self._scrape_article_content(item_id)
            if content:
                return {
                    "url": item_id,
                    "content": content,
                    "source": "web_scraper",
                    "scraped_at": datetime.now().isoformat()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching details for {item_id}: {e}")
            return None
