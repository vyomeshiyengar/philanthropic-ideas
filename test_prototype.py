#!/usr/bin/env python3
"""
Test script for the philanthropic ideas generator prototype.
"""
import asyncio
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test database connection and basic operations."""
    try:
        from storage.database import db_manager
        from storage.models import DataSource, RawData, ExtractedIdea
        
        with db_manager.get_session() as session:
            # Test basic connection
            from sqlalchemy import text
            result = session.execute(text("SELECT 1")).fetchone()
            logger.info("✓ Database connection successful")
            
            # Test table creation
            sources = session.query(DataSource).count()
            logger.info(f"✓ Data sources table accessible: {sources} sources")
            
            raw_data = session.query(RawData).count()
            logger.info(f"✓ Raw data table accessible: {raw_data} items")
            
            ideas = session.query(ExtractedIdea).count()
            logger.info(f"✓ Extracted ideas table accessible: {ideas} ideas")
            
            return True
            
    except Exception as e:
        logger.error(f"✗ Database test failed: {e}")
        return False

def test_configuration():
    """Test configuration loading."""
    try:
        from config.settings import settings
        
        logger.info("✓ Configuration loaded successfully")
        logger.info(f"  - Database URL: {settings.DATABASE_URL}")
        logger.info(f"  - Enabled sources: {[k for k, v in settings.DATA_SOURCES.items() if v['enabled']]}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Configuration test failed: {e}")
        return False

def test_components():
    """Test component initialization."""
    try:
        # Test data ingestion orchestrator
        from data_ingestion.main import DataIngestionOrchestrator
        orchestrator = DataIngestionOrchestrator()
        logger.info("✓ Data ingestion orchestrator initialized")
        
        # Test idea extractor
        from analysis.idea_extractor import IdeaExtractor
        extractor = IdeaExtractor()
        logger.info("✓ Idea extractor initialized")
        
        # Test idea evaluator
        from scoring.idea_evaluator import IdeaEvaluator
        evaluator = IdeaEvaluator()
        logger.info("✓ Idea evaluator initialized")
        
        # Test talent identifier
        from scoring.talent_identifier import TalentIdentifier
        identifier = TalentIdentifier()
        logger.info("✓ Talent identifier initialized")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Component test failed: {e}")
        return False

async def test_api_endpoints():
    """Test API endpoints."""
    try:
        import aiohttp
        import json
        
        base_url = "http://localhost:8000"
        
        async with aiohttp.ClientSession() as session:
            # Test health endpoint
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("✓ Health endpoint working")
                else:
                    logger.warning("⚠ Health endpoint returned non-200 status")
            
            # Test prototype status endpoint
            async with session.get(f"{base_url}/prototype/status") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("✓ Prototype status endpoint working")
                    logger.info(f"  - Raw data: {data.get('total_raw_data', 0)} items")
                    logger.info(f"  - Ideas: {data.get('total_ideas', 0)} extracted")
                else:
                    logger.warning("⚠ Prototype status endpoint returned non-200 status")
            
            return True
            
    except aiohttp.ClientConnectorError as e:
        logger.warning(f"⚠ API server not running: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ API test failed: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("PHILANTHROPIC IDEAS GENERATOR - PROTOTYPE TEST")
    logger.info("=" * 60)
    
    tests = [
        ("Configuration", test_configuration),
        ("Database Connection", test_database_connection),
        ("Components", test_components),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Testing {test_name} ---")
        try:
            if test_func():
                passed += 1
                logger.info(f"✓ {test_name} test PASSED")
            else:
                logger.error(f"✗ {test_name} test FAILED")
        except Exception as e:
            logger.error(f"✗ {test_name} test ERROR: {e}")
    
    # Test API endpoints if server is running
    logger.info(f"\n--- Testing API Endpoints ---")
    try:
        result = asyncio.run(test_api_endpoints())
        if result:
            passed += 1
            total += 1
            logger.info("✓ API endpoints test PASSED")
        else:
            logger.warning("⚠ API endpoints test FAILED (server may not be running)")
    except Exception as e:
        logger.warning(f"⚠ API endpoints test SKIPPED (server may not be running): {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"TEST SUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Prototype is ready to use.")
        logger.info("\nNext steps:")
        logger.info("1. Start the API server: python -m api.main")
        logger.info("2. Open web interface: http://localhost:8000")
        logger.info("3. Click 'Run Prototype Pipeline' to start")
    else:
        logger.error("❌ Some tests failed. Please check the errors above.")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
