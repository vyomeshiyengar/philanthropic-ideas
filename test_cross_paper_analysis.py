#!/usr/bin/env python3
"""
Test script to verify enhanced cross-paper analysis without OpenAI.
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

def test_cross_paper_analysis():
    """Test the enhanced cross-paper analysis functionality."""
    print("🧪 Testing Enhanced Cross-Paper Analysis")
    print("=" * 60)
    
    # Initialize the hybrid extractor (without OpenAI)
    print("🔧 Initializing Hybrid Extractor (Traditional NLP + Cross-Paper Analysis)...")
    extractor = HybridIdeaExtractor(ai_provider="openai")  # Will fall back to traditional methods
    
    # Get raw data for testing
    print("\n📊 Getting raw data for cross-paper analysis...")
    with db_manager.get_session() as session:
        # Get items from different domains for better cross-paper analysis
        raw_data = session.query(RawData).limit(20).all()
        
        if not raw_data:
            print("❌ No raw data found in database")
            return False
        
        print(f"✅ Found {len(raw_data)} raw data items")
        
        # Show some examples
        print("\n📚 Sample raw data for cross-paper analysis:")
        for i, item in enumerate(raw_data[:5], 1):
            print(f"   {i}. {item.title[:80]}...")
            if item.abstract:
                print(f"      Abstract: {item.abstract[:100]}...")
    
    # Test the enhanced cross-paper synthesis
    print("\n🔄 Testing Enhanced Cross-Paper Synthesis...")
    try:
        # Test the fallback synthetic ideas (enhanced version)
        synthetic_ideas = extractor._generate_fallback_synthetic_ideas(raw_data)
        
        if synthetic_ideas:
            print(f"✅ Generated {len(synthetic_ideas)} cross-paper synthetic ideas")
            print("\n💡 Sample Cross-Paper Ideas:")
            for i, idea in enumerate(synthetic_ideas[:5], 1):
                print(f"\n   {i}. {idea.get('title', 'N/A')}")
                print(f"      Domain: {idea.get('domain', 'N/A')}")
                print(f"      Confidence: {idea.get('confidence_score', 'N/A')}")
                print(f"      Method: {idea.get('extraction_method', 'N/A')}")
                if idea.get('key_innovation'):
                    print(f"      Innovation: {idea.get('key_innovation', '')[:100]}...")
                if idea.get('thought_process'):
                    print(f"      Process: {idea.get('thought_process', '')[:100]}...")
                if idea.get('description'):
                    print(f"      Description: {idea.get('description', '')[:150]}...")
        else:
            print("❌ No cross-paper synthetic ideas generated")
            return False
            
    except Exception as e:
        print(f"❌ Cross-paper synthesis failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test full hybrid extraction with cross-paper analysis
    print("\n🔄 Testing Full Hybrid Extraction with Cross-Paper Analysis...")
    try:
        all_ideas = extractor.extract_ideas_from_raw_data()
        
        if all_ideas:
            print(f"✅ Generated {len(all_ideas)} total ideas using enhanced hybrid approach")
            
            # Count by extraction method
            method_counts = {}
            for idea in all_ideas:
                method = idea.get('extraction_method', 'unknown')
                method_counts[method] = method_counts.get(method, 0) + 1
            
            print("\n📈 Ideas by extraction method:")
            for method, count in method_counts.items():
                print(f"   {method}: {count} ideas")
            
            # Show cross-paper analysis ideas specifically
            cross_paper_ideas = [idea for idea in all_ideas if 'cross_paper' in idea.get('extraction_method', '')]
            if cross_paper_ideas:
                print(f"\n🔬 Cross-Paper Analysis Ideas ({len(cross_paper_ideas)}):")
                for i, idea in enumerate(cross_paper_ideas[:3], 1):
                    print(f"   {i}. {idea.get('title', 'N/A')} (Score: {idea.get('confidence_score', 'N/A')})")
                    print(f"      Method: {idea.get('extraction_method', 'N/A')}")
                    if idea.get('thought_process'):
                        print(f"      Analysis: {idea.get('thought_process', '')[:100]}...")
            
            # Show high-confidence ideas
            high_conf_ideas = [idea for idea in all_ideas if idea.get('confidence_score', 0) > 0.7]
            if high_conf_ideas:
                print(f"\n🏆 High-Confidence Ideas ({len(high_conf_ideas)}):")
                for i, idea in enumerate(high_conf_ideas[:3], 1):
                    print(f"   {i}. {idea.get('title', 'N/A')} (Score: {idea.get('confidence_score', 'N/A')})")
                    print(f"      Method: {idea.get('extraction_method', 'N/A')}")
        else:
            print("❌ No ideas generated from enhanced hybrid extraction")
            return False
            
    except Exception as e:
        print(f"❌ Full hybrid extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n✅ Enhanced cross-paper analysis test completed successfully!")
    return True

def test_specific_cross_paper_methods():
    """Test specific cross-paper analysis methods."""
    print("\n🔬 Testing Specific Cross-Paper Analysis Methods")
    print("=" * 60)
    
    extractor = HybridIdeaExtractor(ai_provider="openai")
    
    with db_manager.get_session() as session:
        raw_data = session.query(RawData).limit(10).all()
        
        if not raw_data:
            print("❌ No raw data for testing")
            return False
        
        # Test domain grouping
        print("\n📊 Testing Domain Grouping...")
        domain_groups = extractor._group_sources_by_domain(raw_data)
        for domain, sources in domain_groups.items():
            print(f"   {domain}: {len(sources)} sources")
        
        # Test cross-paper context analysis
        print("\n🔍 Testing Cross-Paper Context Analysis...")
        for domain, sources in domain_groups.items():
            if len(sources) >= 2:
                insights = extractor._analyze_cross_paper_context_simple(sources, domain)
                print(f"\n   Domain: {domain}")
                print(f"   Sources analyzed: {insights.get('source_count', 0)}")
                print(f"   Patterns found: {len(insights.get('patterns', {}).get('common_methods', []))} common methods")
                print(f"   Gaps identified: {len(insights.get('gaps', []))}")
                print(f"   Synergies found: {len(insights.get('synergies', []))}")
                
                # Show some specific insights
                if insights.get('gaps'):
                    print(f"   Sample gap: {insights['gaps'][0].get('description', 'N/A')}")
                if insights.get('synergies'):
                    print(f"   Sample synergy: {insights['synergies'][0].get('description', 'N/A')}")
                break
    
    return True

def main():
    """Main test function."""
    print("🚀 Testing Enhanced Cross-Paper Analysis")
    print("=" * 60)
    
    # Test the enhanced cross-paper analysis
    success1 = test_cross_paper_analysis()
    
    # Test specific methods
    success2 = test_specific_cross_paper_methods()
    
    if success1 and success2:
        print("\n🎉 All tests passed! The enhanced cross-paper analysis is working correctly.")
        print("💡 The hybrid extractor is now using:")
        print("   • Traditional NLP for basic idea extraction")
        print("   • Enhanced cross-paper analysis for contextual synthesis")
        print("   • Pattern recognition across multiple papers")
        print("   • Gap identification and synergy detection")
        print("   • Method-outcome combination analysis")
    else:
        print("\n❌ Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    main()
