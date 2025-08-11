import json
import hashlib
import logging
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
import pickle
import os

logger = logging.getLogger(__name__)

class APICache:
    """Cache for API responses to improve performance and respect rate limits."""
    
    def __init__(self, cache_dir: str = ".cache", default_ttl: int = 3600):
        """
        Initialize the cache.
        
        Args:
            cache_dir: Directory to store cache files
            default_ttl: Default time-to-live in seconds (1 hour)
        """
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        self._ensure_cache_dir()
        
    def _ensure_cache_dir(self):
        """Ensure the cache directory exists."""
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def _get_cache_key(self, source: str, query: str, params: Optional[Dict] = None) -> str:
        """Generate a cache key for the request."""
        # Create a unique key based on source, query, and parameters
        key_data = {
            "source": source,
            "query": query,
            "params": params or {}
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
        
    def _get_cache_file_path(self, cache_key: str) -> str:
        """Get the file path for a cache key."""
        return os.path.join(self.cache_dir, f"{cache_key}.cache")
        
    def get(self, source: str, query: str, params: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Get cached response if available and not expired.
        
        Args:
            source: API source name
            query: Search query
            params: Additional parameters
            
        Returns:
            Cached response data or None if not found/expired
        """
        try:
            cache_key = self._get_cache_key(source, query, params)
            cache_file = self._get_cache_file_path(cache_key)
            
            if not os.path.exists(cache_file):
                return None
                
            # Check if cache is expired
            file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
            if file_age.total_seconds() > self.default_ttl:
                logger.debug(f"Cache expired for {source}:{query}")
                os.remove(cache_file)
                return None
                
            # Load cached data
            with open(cache_file, 'rb') as f:
                cached_data = pickle.load(f)
                
            logger.debug(f"Cache hit for {source}:{query}")
            return cached_data
            
        except Exception as e:
            logger.warning(f"Error reading cache for {source}:{query}: {e}")
            return None
            
    def set(self, source: str, query: str, data: Dict[str, Any], 
            params: Optional[Dict] = None, ttl: Optional[int] = None) -> bool:
        """
        Cache a response.
        
        Args:
            source: API source name
            query: Search query
            data: Response data to cache
            params: Additional parameters
            ttl: Time-to-live in seconds (overrides default)
            
        Returns:
            True if successfully cached, False otherwise
        """
        try:
            cache_key = self._get_cache_key(source, query, params)
            cache_file = self._get_cache_file_path(cache_key)
            
            # Prepare cache entry
            cache_entry = {
                "source": source,
                "query": query,
                "params": params,
                "data": data,
                "cached_at": datetime.now().isoformat(),
                "ttl": ttl or self.default_ttl
            }
            
            # Save to file
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_entry, f)
                
            logger.debug(f"Cached response for {source}:{query}")
            return True
            
        except Exception as e:
            logger.warning(f"Error caching response for {source}:{query}: {e}")
            return False
            
    def invalidate(self, source: str, query: str, params: Optional[Dict] = None) -> bool:
        """
        Remove a cached response.
        
        Args:
            source: API source name
            query: Search query
            params: Additional parameters
            
        Returns:
            True if successfully removed, False otherwise
        """
        try:
            cache_key = self._get_cache_key(source, query, params)
            cache_file = self._get_cache_file_path(cache_key)
            
            if os.path.exists(cache_file):
                os.remove(cache_file)
                logger.debug(f"Invalidated cache for {source}:{query}")
                return True
                
            return False
            
        except Exception as e:
            logger.warning(f"Error invalidating cache for {source}:{query}: {e}")
            return False
            
    def clear(self, source: Optional[str] = None) -> int:
        """
        Clear cache entries.
        
        Args:
            source: If provided, only clear entries for this source
            
        Returns:
            Number of entries cleared
        """
        try:
            cleared_count = 0
            
            for filename in os.listdir(self.cache_dir):
                if not filename.endswith('.cache'):
                    continue
                    
                cache_file = os.path.join(self.cache_dir, filename)
                
                try:
                    with open(cache_file, 'rb') as f:
                        cache_entry = pickle.load(f)
                        
                    # Check if we should clear this entry
                    if source is None or cache_entry.get("source") == source:
                        os.remove(cache_file)
                        cleared_count += 1
                        
                except Exception:
                    # If we can't read the file, remove it anyway
                    os.remove(cache_file)
                    cleared_count += 1
                    
            logger.info(f"Cleared {cleared_count} cache entries")
            return cleared_count
            
        except Exception as e:
            logger.warning(f"Error clearing cache: {e}")
            return 0
            
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            total_files = 0
            total_size = 0
            source_counts = {}
            
            for filename in os.listdir(self.cache_dir):
                if not filename.endswith('.cache'):
                    continue
                    
                cache_file = os.path.join(self.cache_dir, filename)
                total_files += 1
                total_size += os.path.getsize(cache_file)
                
                try:
                    with open(cache_file, 'rb') as f:
                        cache_entry = pickle.load(f)
                        source = cache_entry.get("source", "unknown")
                        source_counts[source] = source_counts.get(source, 0) + 1
                except Exception:
                    pass
                    
            return {
                "total_entries": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "source_counts": source_counts
            }
            
        except Exception as e:
            logger.warning(f"Error getting cache stats: {e}")
            return {"error": str(e)}

# Global cache instance
api_cache = APICache()
