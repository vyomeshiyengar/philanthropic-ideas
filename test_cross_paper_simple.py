#!/usr/bin/env python3
"""
Simple test for cross-paper analysis without SQLAlchemy session issues.
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

def test_cross_paper_analysis_simple():
    """Test the enhanced cross-paper analysis functionality."""
    print("🧪 Testing Enhanced Cross-Paper Analysis (Simple)")
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
        
        # Test the enhanced cross-paper synthesis within the session
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
                print(f"   Common themes: {len(insights.get('common_themes', []))}")
                print(f"   Frequent concepts: {len(insights.get('frequent_concepts', []))}")
                print(f"   Rare concepts: {len(insights.get('rare_concepts', []))}")
                print(f"   Complementary pairs: {len(insights.get('complementary_pairs', []))}")
                
                # Show some specific insights
                if insights.get('common_themes'):
                    print(f"   Sample common theme: {insights['common_themes'][0]}")
                if insights.get('complementary_pairs'):
                    pair = insights['complementary_pairs'][0]
                    print(f"   Sample complementary pair: {pair[0]} + {pair[1]}")
                break
    
    print("\n✅ Enhanced cross-paper analysis test completed successfully!")
    return True

def main():
    """Main test function."""
    print("🚀 Testing Enhanced Cross-Paper Analysis (Simple)")
    print("=" * 60)
    
    # Test the enhanced cross-paper analysis
    success = test_cross_paper_analysis_simple()
    
    if success:
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
