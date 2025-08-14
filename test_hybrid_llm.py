#!/usr/bin/env python3
"""
Test script to verify the hybrid LLM synthesis is working properly.
"""
import os
import sys
import logging
from typing import List, Dict, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analysis.hybrid_idea_extractor import HybridIdeaExtractor
from storage.database import db_manager
from storage.models import RawData
from config.settings import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_hybrid_llm_synthesis():
    """Test the hybrid LLM synthesis functionality."""
    print("🧪 Testing Hybrid LLM Synthesis")
    print("=" * 60)
    
    # Initialize the hybrid extractor
    print("🔧 Initializing Hybrid Extractor...")
    extractor = HybridIdeaExtractor(ai_provider="openai")
    
    # Check AI client status
    if extractor.ai_client:
        print("✅ AI client initialized successfully")
        print(f"   Provider: {extractor.ai_provider}")
    else:
        print("❌ AI client not available")
        print("   This means the hybrid extractor will fall back to traditional NLP only")
        print("   To enable LLM synthesis, you need a valid OpenAI API key")
        return False
    
    # Get some raw data for testing
    print("\n📊 Getting raw data for synthesis...")
    with db_manager.get_session() as session:
        # Get a few items from different domains
        raw_data = session.query(RawData).limit(10).all()
        
        if not raw_data:
            print("❌ No raw data found in database")
            return False
        
        print(f"✅ Found {len(raw_data)} raw data items")
        
        # Show some examples
        print("\n📚 Sample raw data:")
        for i, item in enumerate(raw_data[:3], 1):
            print(f"   {i}. {item.title[:80]}...")
            if item.abstract:
                print(f"      Abstract: {item.abstract[:100]}...")
    
    # Test AI synthesis
    print("\n🤖 Testing AI Synthesis...")
    try:
        synthetic_ideas = extractor._generate_synthetic_ideas(raw_data)
        
        if synthetic_ideas:
            print(f"✅ Generated {len(synthetic_ideas)} AI-synthesized ideas")
            print("\n💡 Sample AI-synthesized ideas:")
            for i, idea in enumerate(synthetic_ideas[:3], 1):
                print(f"\n   {i}. {idea.get('title', 'N/A')}")
                print(f"      Domain: {idea.get('domain', 'N/A')}")
                print(f"      Confidence: {idea.get('confidence_score', 'N/A')}")
                print(f"      Method: {idea.get('extraction_method', 'N/A')}")
                if idea.get('key_innovation'):
                    print(f"      Innovation: {idea.get('key_innovation', '')[:100]}...")
                if idea.get('thought_process'):
                    print(f"      Process: {idea.get('thought_process', '')[:100]}...")
        else:
            print("❌ No AI-synthesized ideas generated")
            return False
            
    except Exception as e:
        print(f"❌ AI synthesis failed: {e}")
        return False
    
    # Test full hybrid extraction
    print("\n🔄 Testing Full Hybrid Extraction...")
    try:
        all_ideas = extractor.extract_ideas_from_raw_data()
        
        if all_ideas:
            print(f"✅ Generated {len(all_ideas)} total ideas using hybrid approach")
            
            # Count by extraction method
            method_counts = {}
            for idea in all_ideas:
                method = idea.get('extraction_method', 'unknown')
                method_counts[method] = method_counts.get(method, 0) + 1
            
            print("\n📈 Ideas by extraction method:")
            for method, count in method_counts.items():
                print(f"   {method}: {count} ideas")
            
            # Show some high-confidence ideas
            high_conf_ideas = [idea for idea in all_ideas if idea.get('confidence_score', 0) > 0.7]
            if high_conf_ideas:
                print(f"\n🏆 High-confidence ideas ({len(high_conf_ideas)}):")
                for i, idea in enumerate(high_conf_ideas[:3], 1):
                    print(f"   {i}. {idea.get('title', 'N/A')} (Score: {idea.get('confidence_score', 'N/A')})")
                    print(f"      Method: {idea.get('extraction_method', 'N/A')}")
        else:
            print("❌ No ideas generated from hybrid extraction")
            return False
            
    except Exception as e:
        print(f"❌ Full hybrid extraction failed: {e}")
        return False
    
    print("\n✅ Hybrid LLM synthesis test completed successfully!")
    return True

def test_openai_api_key():
    """Test if the OpenAI API key is valid."""
    print("\n🔑 Testing OpenAI API Key...")
    
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        print("❌ No OpenAI API key found in settings")
        return False
    
    print(f"✅ API key found: {api_key[:20]}...{api_key[-4:]}")
    
    # Test the API key
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        # Simple test call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'Hello World'"}],
            max_tokens=10
        )
        
        content = response.choices[0].message.content
        print(f"✅ API key is valid! Response: {content}")
        return True
        
    except Exception as e:
        print(f"❌ API key is invalid: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 Testing Hybrid LLM Synthesis")
    print("=" * 60)
    
    # First test the API key
    api_key_valid = test_openai_api_key()
    
    if not api_key_valid:
        print("\n💡 To enable LLM synthesis, you need to:")
        print("   1. Get a valid OpenAI API key from https://platform.openai.com/api-keys")
        print("   2. Update the OPENAI_API_KEY in your .env file")
        print("   3. Restart the application")
        return
    
    # Test the hybrid synthesis
    success = test_hybrid_llm_synthesis()
    
    if success:
        print("\n🎉 All tests passed! The hybrid LLM synthesis is working correctly.")
        print("💡 The hybrid extractor is now using:")
        print("   • Traditional NLP for basic idea extraction")
        print("   • AI synthesis for cross-paper insights")
        print("   • Pattern recognition for gap identification")
    else:
        print("\n❌ Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    main()
