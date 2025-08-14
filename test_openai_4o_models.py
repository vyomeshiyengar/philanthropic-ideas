#!/usr/bin/env python3
"""
Test script for OpenAI 4o-mini and 4o models integration.
"""
import sys
import os
import logging
from typing import List, Dict, Any

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analysis.hybrid_idea_extractor import HybridIdeaExtractor
from storage.database import db_manager
from storage.models import RawData
from config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_openai_models():
    """Test the OpenAI 4o-mini and 4o models integration."""
    print("🧪 Testing OpenAI 4o-mini and 4o Models Integration")
    print("=" * 60)
    
    # Check if OpenAI API key is available
    if not settings.OPENAI_API_KEY:
        print("❌ OpenAI API key not found in settings")
        print("Please set OPENAI_API_KEY in your .env file")
        return False
    
    print(f"✅ OpenAI API key found: {settings.OPENAI_API_KEY[:20]}...")
    
    # Initialize the hybrid extractor
    try:
        extractor = HybridIdeaExtractor(ai_provider="openai")
        print("✅ HybridIdeaExtractor initialized successfully")
        
        # Check if AI client is available
        if not extractor.ai_client:
            print("❌ AI client not available")
            return False
        
        print("✅ AI client available")
        print(f"📋 Model configuration:")
        print(f"   - Data ingestion: {extractor.models['data_ingestion']}")
        print(f"   - Idea synthesis: {extractor.models['idea_synthesis']}")
        
    except Exception as e:
        print(f"❌ Failed to initialize HybridIdeaExtractor: {e}")
        return False
    
    # Test data ingestion with 4o-mini
    print("\n🔍 Testing 4o-mini for data ingestion...")
    test_text = """
    A recent study on malaria prevention in sub-Saharan Africa found that 
    distributing insecticide-treated bed nets reduced malaria incidence by 45% 
    in communities where they were widely adopted. The intervention cost $5 per 
    net and lasted for 3 years, making it highly cost-effective.
    """
    
    try:
        ingestion_ideas = extractor._call_ai_for_data_ingestion(test_text, "health")
        print(f"✅ 4o-mini data ingestion successful: {len(ingestion_ideas)} ideas generated")
        
        for i, idea in enumerate(ingestion_ideas, 1):
            print(f"   Idea {i}: {idea.get('title', 'No title')}")
            print(f"   Method: {idea.get('extraction_method', 'Unknown')}")
            print(f"   Confidence: {idea.get('confidence_score', 0):.2f}")
        
    except Exception as e:
        print(f"❌ 4o-mini data ingestion failed: {e}")
        return False
    
    # Test idea synthesis with 4o
    print("\n🧠 Testing 4o for idea synthesis...")
    test_context = """
    Source 1: Malaria Prevention with Bed Nets
    Abstract: Study shows 45% reduction in malaria with $5 bed nets...
    
    Source 2: Community Health Workers
    Abstract: Training local health workers improved health outcomes by 30%...
    
    Source 3: Mobile Health Interventions
    Abstract: SMS reminders increased vaccination rates by 25%...
    """
    
    try:
        synthesis_ideas = extractor._call_ai_for_synthesis(test_context, "health")
        print(f"✅ 4o idea synthesis successful: {len(synthesis_ideas)} ideas generated")
        
        for i, idea in enumerate(synthesis_ideas, 1):
            print(f"   Idea {i}: {idea.get('title', 'No title')}")
            print(f"   Method: {idea.get('extraction_method', 'Unknown')}")
            print(f"   Confidence: {idea.get('confidence_score', 0):.2f}")
        
    except Exception as e:
        print(f"❌ 4o idea synthesis failed: {e}")
        return False
    
    # Test with real data from database
    print("\n📊 Testing with real database data...")
    try:
        with db_manager.get_session() as session:
            # Get a few raw data items
            raw_data_items = session.query(RawData).limit(3).all()
            
            if raw_data_items:
                print(f"✅ Found {len(raw_data_items)} raw data items for testing")
                
                # Test extraction on one item
                test_item = raw_data_items[0]
                print(f"   Testing with: {test_item.title[:50]}...")
                
                # Test AI ingestion on this item
                text_content = f"{test_item.title} {test_item.abstract or ''}"
                domain = extractor._classify_domain(text_content, extractor.nlp(text_content))
                
                if domain:
                    ai_ideas = extractor._call_ai_for_data_ingestion(text_content, domain)
                    print(f"   ✅ AI ingestion generated {len(ai_ideas)} ideas for {domain} domain")
                else:
                    print("   ⚠️ Could not classify domain for test item")
            else:
                print("⚠️ No raw data found in database")
                
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    
    print("\n🎉 All tests completed successfully!")
    print("✅ OpenAI 4o-mini and 4o models are working correctly")
    return True

def test_cost_efficiency():
    """Test the cost efficiency of the model selection."""
    print("\n💰 Cost Efficiency Analysis")
    print("=" * 40)
    
    print("📊 Model Cost Comparison (approximate):")
    print("   - gpt-4o-mini: ~$0.15 per 1M input tokens")
    print("   - gpt-4o: ~$2.50 per 1M input tokens")
    print("   - Cost ratio: 4o-mini is ~16x cheaper than 4o")
    
    print("\n🎯 Usage Strategy:")
    print("   - 4o-mini: Data ingestion, individual item analysis")
    print("   - 4o: High-quality idea synthesis, complex reasoning")
    print("   - This optimizes cost while maintaining quality")

if __name__ == "__main__":
    print("🚀 OpenAI 4o Models Integration Test")
    print("=" * 50)
    
    success = test_openai_models()
    
    if success:
        test_cost_efficiency()
        print("\n✅ Integration test completed successfully!")
        print("The hybrid extractor is ready to use with OpenAI 4o models.")
    else:
        print("\n❌ Integration test failed!")
        print("Please check your OpenAI API key and try again.")
        sys.exit(1)
