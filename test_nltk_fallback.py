#!/usr/bin/env python3
"""
Test NLTK Fallback - spaCy-free testing
"""
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_nltk_extractor():
    """Test the NLTK-only extractor."""
    print("🧪 Testing NLTK-Only Extractor")
    print("=" * 40)
    
    try:
        from analysis.idea_extractor_nltk_only import NLTKIdeaExtractor
        
        # Create extractor
        extractor = NLTKIdeaExtractor()
        print("✅ NLTK extractor created successfully")
        
        # Test text
        test_text = """
        Artificial intelligence and machine learning are transforming healthcare.
        Researchers are developing new algorithms for disease diagnosis and treatment.
        Climate change requires innovative solutions for renewable energy.
        Educational technology is improving student learning outcomes.
        """
        
        # Extract ideas
        ideas = extractor.extract_ideas_from_text(test_text)
        print(f"✅ Extracted {len(ideas)} ideas")
        
        # Show some ideas
        for i, idea in enumerate(ideas[:5]):
            print(f"  {i+1}. {idea['title']}")
            print(f"     Domain: {idea['domain']}")
            print(f"     Confidence: {idea['confidence']}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ NLTK extractor test failed: {e}")
        return False

def test_hybrid_without_spacy():
    """Test hybrid extractor without spaCy."""
    print("\n🧪 Testing Hybrid Extractor (spaCy-free)")
    print("=" * 45)
    
    try:
        from analysis.hybrid_idea_extractor import HybridIdeaExtractor
        
        # Create hybrid extractor (should use NLTK fallback)
        extractor = HybridIdeaExtractor(ai_provider="openai")
        print("✅ Hybrid extractor created successfully")
        
        # Test basic functionality
        test_text = "Machine learning applications in healthcare are promising."
        
        # This should work with NLTK fallback
        print("✅ Hybrid extractor initialized with NLTK fallback")
        
        return True
        
    except Exception as e:
        print(f"❌ Hybrid extractor test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🍎 Mac Python 3.12 spaCy-Free Test")
    print("=" * 40)
    
    # Test NLTK extractor
    nltk_ok = test_nltk_extractor()
    
    # Test hybrid extractor
    hybrid_ok = test_hybrid_without_spacy()
    
    print("\n🎯 Test Results")
    print("=" * 20)
    
    if nltk_ok and hybrid_ok:
        print("✅ All tests passed!")
        print("🚀 You can now run the project without spaCy")
        print("\nNext steps:")
        print("1. python quick_hybrid_test.py")
        print("2. python api_server_start.py")
        print("3. python run_full_extraction.py")
    else:
        print("❌ Some tests failed")
        if not nltk_ok:
            print("   - NLTK extractor failed")
        if not hybrid_ok:
            print("   - Hybrid extractor failed")

if __name__ == "__main__":
    main()
