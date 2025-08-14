#!/usr/bin/env python3
"""
Script to regenerate ideas using enhanced cross-paper analysis.
"""
import os
import sys
import logging
from typing import List, Dict, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analysis.hybrid_idea_extractor import HybridIdeaExtractor
from storage.database import db_manager
from storage.models import RawData, ExtractedIdea
from sqlalchemy import delete

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def regenerate_ideas_with_cross_paper_analysis():
    """Regenerate ideas using enhanced cross-paper analysis."""
    print("🔄 Regenerating Ideas with Enhanced Cross-Paper Analysis")
    print("=" * 60)
    
    # Initialize the hybrid extractor
    print("🔧 Initializing Enhanced Hybrid Extractor...")
    extractor = HybridIdeaExtractor(ai_provider="openai")  # Will use enhanced cross-paper analysis
    
    # Get raw data
    print("\n📊 Getting raw data for idea regeneration...")
    with db_manager.get_session() as session:
        raw_data = session.query(RawData).all()
        
        if not raw_data:
            print("❌ No raw data found in database")
            return False
        
        print(f"✅ Found {len(raw_data)} raw data items")
        
        # Create a mapping of raw data by domain for proper assignment
        raw_data_by_domain = {}
        for item in raw_data:
            # Determine domain from title/abstract content
            text_content = f"{item.title} {item.abstract or ''}"
            doc = extractor.nlp(text_content)
            domain = extractor._classify_domain(text_content, doc)
            if domain not in raw_data_by_domain:
                raw_data_by_domain[domain] = []
            raw_data_by_domain[domain].append(item)
        
        print(f"📊 Grouped raw data into {len(raw_data_by_domain)} domains")
        for domain, items in raw_data_by_domain.items():
            print(f"   {domain}: {len(items)} items")
        
        # Clear existing ideas
        print("\n🗑️  Clearing existing ideas...")
        session.execute(delete(ExtractedIdea))
        session.commit()
        print("✅ Cleared existing ideas")
        
        # Generate new ideas using enhanced cross-paper analysis
        print("\n🔄 Generating new ideas with enhanced cross-paper analysis...")
        print("⏳ This may take several minutes due to cross-paper analysis...")
        try:
            new_ideas = extractor.extract_ideas_from_raw_data()
            
            if new_ideas:
                print(f"✅ Generated {len(new_ideas)} new ideas using enhanced cross-paper analysis")
                
                # Count by extraction method
                method_counts = {}
                for idea in new_ideas:
                    method = idea.get('extraction_method', 'unknown')
                    method_counts[method] = method_counts.get(method, 0) + 1
                
                print("\n📈 Ideas by extraction method:")
                for method, count in method_counts.items():
                    print(f"   {method}: {count} ideas")
                
                # Show cross-paper analysis ideas specifically
                cross_paper_ideas = [idea for idea in new_ideas if 'cross_paper' in idea.get('extraction_method', '')]
                if cross_paper_ideas:
                    print(f"\n🔬 Cross-Paper Analysis Ideas ({len(cross_paper_ideas)}):")
                    for i, idea in enumerate(cross_paper_ideas[:5], 1):
                        print(f"   {i}. {idea.get('title', 'N/A')} (Score: {idea.get('confidence_score', 'N/A')})")
                        print(f"      Method: {idea.get('extraction_method', 'N/A')}")
                        if idea.get('thought_process'):
                            print(f"      Analysis: {idea.get('thought_process', '')[:100]}...")
                
                # Save new ideas to database with proper raw_data_id assignment
                print("\n💾 Saving new ideas to database...")
                saved_count = 0
                for idea_data in new_ideas:
                    try:
                        # Find appropriate raw_data_id based on domain
                        domain = idea_data.get('domain', '')
                        raw_data_id = 1  # Default fallback
                        
                        if domain in raw_data_by_domain and raw_data_by_domain[domain]:
                            # Use the first item from the same domain
                            raw_data_id = raw_data_by_domain[domain][0].id
                        
                        # Only use fields that exist in the ExtractedIdea model
                        idea = ExtractedIdea(
                            title=idea_data.get('title', ''),
                            description=idea_data.get('description', ''),
                            domain=idea_data.get('domain', ''),
                            primary_metric=idea_data.get('primary_metric', ''),
                            idea_type=idea_data.get('idea_type', ''),
                            confidence_score=idea_data.get('confidence_score', 0.0),
                            extraction_method=idea_data.get('extraction_method', ''),
                            thought_process=idea_data.get('thought_process', ''),
                            raw_data_id=raw_data_id
                        )
                        session.add(idea)
                        saved_count += 1
                        
                        # Show progress every 10 ideas
                        if saved_count % 10 == 0:
                            print(f"   Saved {saved_count} ideas...")
                            
                    except Exception as e:
                        logger.error(f"Failed to save idea {idea_data.get('title', 'N/A')}: {e}")
                
                session.commit()
                print(f"✅ Saved {saved_count} new ideas to database")
                
                # Show final statistics
                total_ideas = session.query(ExtractedIdea).count()
                print(f"\n📊 Final Statistics:")
                print(f"   Total ideas in database: {total_ideas}")
                print(f"   Cross-paper analysis ideas: {len(cross_paper_ideas)}")
                
                # Show some high-confidence ideas
                high_conf_ideas = session.query(ExtractedIdea).filter(
                    ExtractedIdea.confidence_score >= 0.7
                ).order_by(ExtractedIdea.confidence_score.desc()).limit(5).all()
                
                if high_conf_ideas:
                    print(f"\n🏆 High-Confidence Ideas ({len(high_conf_ideas)}):")
                    for i, idea in enumerate(high_conf_ideas, 1):
                        print(f"   {i}. {idea.title} (Score: {idea.confidence_score:.2f})")
                        print(f"      Method: {idea.extraction_method}")
                        if idea.thought_process:
                            print(f"      Analysis: {idea.thought_process[:100]}...")
                
            else:
                print("❌ No new ideas generated")
                return False
                
        except Exception as e:
            print(f"❌ Idea generation failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print("\n✅ Idea regeneration completed successfully!")
    return True

def main():
    """Main function."""
    print("🚀 Regenerating Ideas with Enhanced Cross-Paper Analysis")
    print("=" * 60)
    
    success = regenerate_ideas_with_cross_paper_analysis()
    
    if success:
        print("\n🎉 Idea regeneration completed successfully!")
        print("💡 The database now contains ideas generated using:")
        print("   • Traditional NLP for basic idea extraction")
        print("   • Enhanced cross-paper analysis for contextual synthesis")
        print("   • Pattern recognition across multiple papers")
        print("   • Gap identification and synergy detection")
        print("   • Method-outcome combination analysis")
        print("\n🌐 You can now view the enhanced ideas in the frontend!")
    else:
        print("\n❌ Idea regeneration failed. Check the logs above for details.")

if __name__ == "__main__":
    main()
