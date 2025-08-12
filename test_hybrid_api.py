#!/usr/bin/env python3
"""
Test script to verify that the API is using the hybrid extractor correctly.
"""
import asyncio
import logging
from analysis.hybrid_idea_extractor import HybridIdeaExtractor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_hybrid_extractor():
    """Test that the hybrid extractor works correctly."""
    print("🧪 Testing Hybrid Extractor API Integration")
    print("=" * 50)
    
    try:
        # Create hybrid extractor
        hybrid_extractor = HybridIdeaExtractor()
        
        print(f"✅ Hybrid extractor created successfully")
        print(f"   AI Client: {'✅ Available' if hybrid_extractor.ai_client else '❌ Not available'}")
        print(f"   NLP Pipeline: {'✅ Available' if hasattr(hybrid_extractor, 'nlp') and hybrid_extractor.nlp else '❌ Not available'}")
        print(f"   Enhanced Keywords: ✅ {len(hybrid_extractor.enhanced_keywords)} domains")
        
        # Test extraction method
        print("\n📝 Testing idea extraction...")
        ideas = hybrid_extractor.extract_ideas_from_raw_data()
        print(f"✅ Extracted {len(ideas)} ideas using hybrid extractor")
        
        if ideas:
            print("\n📋 Sample extracted idea:")
            sample_idea = ideas[0]
            print(f"   Title: {sample_idea.get('title', 'N/A')}")
            print(f"   Domain: {sample_idea.get('domain', 'N/A')}")
            print(f"   Method: {sample_idea.get('extraction_method', 'N/A')}")
            print(f"   Confidence: {sample_idea.get('confidence_score', 'N/A')}")
        
        print("\n🎉 Hybrid extractor test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Hybrid extractor test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_hybrid_extractor()
    exit(0 if success else 1)

