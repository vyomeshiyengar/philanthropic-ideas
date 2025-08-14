#!/usr/bin/env python3
"""
Full extraction script using hybrid system with AI to generate new ideas.
"""
import sys
import os
import time
from datetime import datetime
from typing import List, Dict, Any

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analysis.hybrid_idea_extractor import HybridIdeaExtractor
from storage.database import db_manager
from storage.models import RawData, ExtractedIdea
from config.settings import settings

def run_full_extraction():
    """Run full extraction using hybrid system with AI."""
    print("🚀 Full Hybrid Extraction with AI")
    print("=" * 50)
    print(f"⏰ Started at: {datetime.now().strftime('%H:%M:%S')}")
    
    # Initialize hybrid extractor
    print("\n🔧 Initializing Hybrid Extractor...")
    try:
        extractor = HybridIdeaExtractor(ai_provider="openai")
        print("✅ HybridIdeaExtractor initialized")
        
        if extractor.ai_client:
            print("✅ OpenAI integration active")
            print(f"   📋 Models: {extractor.models}")
        else:
            print("⚠️ OpenAI not available (using fallback methods)")
            
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False
    
    # Check current data status
    print("\n📊 Checking Current Data Status...")
    try:
        with db_manager.get_session() as session:
            raw_count = session.query(RawData).count()
            existing_ideas = session.query(ExtractedIdea).count()
            
            print(f"📈 Raw data items: {raw_count:,}")
            print(f"💡 Existing ideas: {existing_ideas}")
            
            # Check domain distribution
            domains = session.query(RawData.metadata_json).all()
            domain_counts = {}
            for domain_data in domains:
                if domain_data[0] and 'domain' in domain_data[0]:
                    domain = domain_data[0]['domain']
                    domain_counts[domain] = domain_counts.get(domain, 0) + 1
            
            print(f"🌍 Domain distribution:")
            for domain, count in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"   • {domain}: {count:,} items")
                
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False
    
    # Run extraction on a sample of data (to avoid overwhelming the system)
    print("\n🎯 Running Full Extraction...")
    print("Note: Processing a sample of data for efficiency")
    
    try:
        with db_manager.get_session() as session:
            # Get a sample of raw data (limit to avoid overwhelming)
            sample_size = min(100, raw_count)  # Process up to 100 items
            raw_data_items = session.query(RawData).limit(sample_size).all()
            
            print(f"📋 Processing {len(raw_data_items)} items...")
            
            # Run hybrid extraction
            start_time = time.time()
            all_ideas = extractor.extract_ideas_from_raw_data()
            end_time = time.time()
            
            print(f"✅ Extraction completed in {end_time - start_time:.2f}s")
            print(f"💡 Total ideas generated: {len(all_ideas)}")
            
            # Analyze results
            print("\n📊 Extraction Results Analysis...")
            
            # Count by extraction method
            method_counts = {}
            domain_counts = {}
            confidence_scores = []
            
            for idea in all_ideas:
                method = idea.get('extraction_method', 'unknown')
                method_counts[method] = method_counts.get(method, 0) + 1
                
                domain = idea.get('domain', 'unknown')
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
                
                confidence = idea.get('confidence_score', 0)
                confidence_scores.append(confidence)
            
            print(f"🔍 Extraction Methods:")
            for method, count in sorted(method_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"   • {method}: {count} ideas")
            
            print(f"🌍 Domain Distribution:")
            for domain, count in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"   • {domain}: {count} ideas")
            
            if confidence_scores:
                avg_confidence = sum(confidence_scores) / len(confidence_scores)
                print(f"📈 Average confidence: {avg_confidence:.2f}")
            
            # Show top ideas
            print(f"\n🏆 Top Generated Ideas:")
            print("-" * 50)
            
            # Sort by confidence and show top 10
            sorted_ideas = sorted(all_ideas, key=lambda x: x.get('confidence_score', 0), reverse=True)
            
            for i, idea in enumerate(sorted_ideas[:10], 1):
                title = idea.get('title', 'No title')
                domain = idea.get('domain', 'unknown')
                method = idea.get('extraction_method', 'unknown')
                confidence = idea.get('confidence_score', 0)
                
                print(f"{i:2d}. {title}")
                print(f"    Domain: {domain} | Method: {method} | Confidence: {confidence:.2f}")
                print()
            
            # Save ideas to database
            print(f"\n💾 Saving Ideas to Database...")
            saved_count = 0
            
            for idea_data in all_ideas:
                try:
                    # Create ExtractedIdea object
                    idea = ExtractedIdea(
                        title=idea_data.get('title', ''),
                        description=idea_data.get('description', ''),
                        domain=idea_data.get('domain', 'unknown'),
                        primary_metric=idea_data.get('primary_metric', 'unknown'),
                        idea_type=idea_data.get('idea_type', 'unknown'),
                        confidence_score=idea_data.get('confidence_score', 0.5),
                        extraction_method=idea_data.get('extraction_method', 'unknown'),
                        raw_data_id=idea_data.get('raw_data_id'),
                        thought_process=idea_data.get('thought_process', '')
                    )
                    
                    session.add(idea)
                    saved_count += 1
                    
                except Exception as e:
                    print(f"⚠️ Failed to save idea '{idea_data.get('title', 'No title')}': {e}")
                    continue
            
            session.commit()
            print(f"✅ Saved {saved_count} new ideas to database")
            
            # Final status
            final_idea_count = session.query(ExtractedIdea).count()
            print(f"📊 Total ideas in database: {final_idea_count}")
            
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return False
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%H:%M:%S')}")
    return True

def show_extraction_summary():
    """Show summary of extraction results."""
    print("\n📋 Extraction Summary")
    print("=" * 30)
    
    try:
        with db_manager.get_session() as session:
            total_ideas = session.query(ExtractedIdea).count()
            
            # Get recent ideas (last 50)
            recent_ideas = session.query(ExtractedIdea).order_by(
                ExtractedIdea.id.desc()
            ).limit(50).all()
            
            print(f"💡 Total ideas in database: {total_ideas}")
            print(f"🆕 Recent ideas: {len(recent_ideas)}")
            
            # Show some recent high-confidence ideas
            high_confidence = [idea for idea in recent_ideas if idea.confidence_score > 0.7]
            
            if high_confidence:
                print(f"\n🏆 Recent High-Confidence Ideas:")
                for idea in high_confidence[:5]:
                    print(f"   • {idea.title} ({idea.domain}, {idea.confidence_score:.2f})")
            
    except Exception as e:
        print(f"❌ Could not show summary: {e}")

if __name__ == "__main__":
    print("🚀 Starting Full Hybrid Extraction")
    print("=" * 50)
    
    success = run_full_extraction()
    
    if success:
        show_extraction_summary()
        print("\n🎉 Full extraction completed successfully!")
        print("New ideas have been generated and saved to the database.")
        print("You can now view them in the frontend or run evaluations.")
    else:
        print("\n❌ Full extraction failed!")
        print("Check the errors above for issues.")
        sys.exit(1)
