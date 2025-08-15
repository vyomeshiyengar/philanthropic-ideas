#!/usr/bin/env python3
"""
Test script to verify the hybrid extractor fix is working.
"""
import sys
import os
import logging

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_hybrid_extractor():
    """Test the hybrid extractor with the fix."""
    print("🧪 Testing Hybrid Extractor Fix")
    print("=" * 40)
    
    try:
        # Import required modules
        from analysis.hybrid_idea_extractor import HybridIdeaExtractor
        from storage.database import db_manager
        from storage.models import RawData
        
        print("✅ Imports successful")
        
        # Initialize the hybrid extractor
        print("🔧 Initializing hybrid extractor...")
        extractor = HybridIdeaExtractor(ai_provider="openai")
        print("✅ Hybrid extractor initialized")
        
        # Test the extract_ideas_from_raw_data method
        print("🧠 Testing idea extraction...")
        ideas = extractor.extract_ideas_from_raw_data()
        
        print(f"✅ Extracted {len(ideas)} ideas successfully")
        
        if ideas:
            print("📋 Sample ideas:")
            for i, idea in enumerate(ideas[:3], 1):
                print(f"   {i}. {idea.get('title', 'No title')[:60]}...")
                print(f"      Domain: {idea.get('domain', 'Unknown')}")
                print(f"      Confidence: {idea.get('confidence', 0):.2f}")
                print()
        
        # Test saving ideas
        print("💾 Testing idea saving...")
        saved_count = extractor.save_extracted_ideas(ideas)
        print(f"✅ Saved {saved_count} ideas to database")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 Hybrid Extractor Fix Test")
    print("=" * 50)
    
    success = test_hybrid_extractor()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! The hybrid extractor fix is working.")
        print("\n💡 Next steps:")
        print("   1. The full extraction should now work from the frontend")
        print("   2. Click 'Run Full Extraction' in the web interface")
        print("   3. Monitor the terminal for progress updates")
    else:
        print("❌ Tests failed. Please check the error messages above.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

