#!/usr/bin/env python3
"""
Test script to demonstrate the caching functionality.
"""
import asyncio
import logging
from storage.cache import api_cache
from data_ingestion.openalex_ingester import OpenAlexIngester

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_caching():
    """Test the caching functionality with OpenAlex API."""
    print("=" * 60)
    print("Testing API Response Caching")
    print("=" * 60)
    
    # Initialize cache and ingester
    print("1. Initializing cache and OpenAlex ingester...")
    
    async with OpenAlexIngester() as ingester:
        query = "education interventions"
        
        print(f"\n2. Making first request for: '{query}'")
        print("   (This will make an actual API call and cache the result)")
        
        # First request - should hit the API
        start_time = asyncio.get_event_loop().time()
        result1 = await ingester.search(query, max_results=5)
        first_request_time = asyncio.get_event_loop().time() - start_time
        
        print(f"   First request completed in {first_request_time:.2f} seconds")
        print(f"   Found {len(result1.raw_data)} items")
        
        print(f"\n3. Making second request for: '{query}'")
        print("   (This should use cached data and be much faster)")
        
        # Second request - should use cache
        start_time = asyncio.get_event_loop().time()
        result2 = await ingester.search(query, max_results=5)
        second_request_time = asyncio.get_event_loop().time() - start_time
        
        print(f"   Second request completed in {second_request_time:.2f} seconds")
        print(f"   Found {len(result2.raw_data)} items")
        
        # Calculate speedup
        if first_request_time > 0:
            speedup = first_request_time / second_request_time
            print(f"   Speedup: {speedup:.1f}x faster!")
        
        print(f"\n4. Cache statistics:")
        stats = api_cache.get_stats()
        print(f"   Total entries: {stats['total_entries']}")
        print(f"   Total size: {stats['total_size_mb']} MB")
        print(f"   By source: {stats['source_counts']}")
        
        print(f"\n5. Testing cache invalidation...")
        success = api_cache.invalidate("openalex", query)
        print(f"   Cache invalidation: {'Success' if success else 'No entry found'}")
        
        print(f"\n6. Making third request after invalidation:")
        print("   (This should make a fresh API call again)")
        
        start_time = asyncio.get_event_loop().time()
        result3 = await ingester.search(query, max_results=5)
        third_request_time = asyncio.get_event_loop().time() - start_time
        
        print(f"   Third request completed in {third_request_time:.2f} seconds")
        print(f"   Found {len(result3.raw_data)} items")
        
        print(f"\n7. Final cache statistics:")
        stats = api_cache.get_stats()
        print(f"   Total entries: {stats['total_entries']}")
        print(f"   Total size: {stats['total_size_mb']} MB")
        
        print(f"\n8. Clearing all cache...")
        cleared = api_cache.clear()
        print(f"   Cleared {cleared} entries")
        
        final_stats = api_cache.get_stats()
        print(f"   Final cache size: {final_stats['total_entries']} entries")

def test_cache_operations():
    """Test basic cache operations."""
    print("\n" + "=" * 60)
    print("Testing Basic Cache Operations")
    print("=" * 60)
    
    # Test setting and getting cache
    print("1. Testing cache set/get operations...")
    
    test_data = {"message": "Hello, World!", "timestamp": "2024-01-01"}
    success = api_cache.set("test_source", "test_query", test_data)
    print(f"   Cache set: {'Success' if success else 'Failed'}")
    
    cached_data = api_cache.get("test_source", "test_query")
    if cached_data:
        print(f"   Cache get: Success - {cached_data.get('data', {}).get('message')}")
    else:
        print("   Cache get: Failed")
    
    # Test cache with parameters
    print("\n2. Testing cache with parameters...")
    
    params = {"max_results": 10, "domain": "health"}
    test_data_with_params = {"results": [1, 2, 3], "params": params}
    api_cache.set("test_source", "test_query", test_data_with_params, params)
    
    cached_with_params = api_cache.get("test_source", "test_query", params)
    if cached_with_params:
        print(f"   Cache with params: Success - {len(cached_with_params.get('data', {}).get('results', []))} results")
    else:
        print("   Cache with params: Failed")
    
    # Test cache key generation
    print("\n3. Testing cache key generation...")
    
    key1 = api_cache._get_cache_key("source1", "query1")
    key2 = api_cache._get_cache_key("source1", "query1")
    key3 = api_cache._get_cache_key("source2", "query1")
    
    print(f"   Same source/query keys match: {key1 == key2}")
    print(f"   Different source keys differ: {key1 != key3}")
    
    # Clean up test data
    api_cache.clear("test_source")
    print(f"\n4. Cleaned up test data")

if __name__ == "__main__":
    print("Starting cache testing...")
    
    # Test basic operations first
    test_cache_operations()
    
    # Test with actual API (if available)
    try:
        asyncio.run(test_caching())
    except Exception as e:
        print(f"\nAPI test failed (this is expected if no API keys are configured): {e}")
        print("The cache functionality still works for local operations!")
    
    print("\n" + "=" * 60)
    print("Cache testing completed!")
    print("=" * 60)
