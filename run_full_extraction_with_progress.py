#!/usr/bin/env python3
"""
Run Full Extraction with Progress Updates
"""
import sys
import os
import time
import logging
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Run full extraction with progress updates."""
    print("🚀 Full Idea Extraction with Progress")
    print("=" * 50)
    print(f"⏰ Started at: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    try:
        # Import required modules
        from storage.database import db_manager
        from analysis.hybrid_idea_extractor import HybridIdeaExtractor
        from scoring.idea_evaluator import IdeaEvaluator
        
        # Initialize components
        print("1️⃣ Initializing components...")
        extractor = HybridIdeaExtractor(ai_provider="openai")
        evaluator = IdeaEvaluator()
        
        from storage.models import RawData
        with db_manager.get_session() as session:
            raw_count = session.query(RawData).count()
            print(f"   📊 Found {raw_count} raw data items")
        
        print("✅ Components initialized")
        print()
        
        # Step 1: AI Processing and Cross-Paper Analysis
        print("2️⃣ AI Processing and Cross-Paper Analysis...")
        print("   🔄 Processing raw data with AI and cross-paper analysis...")
        
        # Get a sample of raw data for processing
        with db_manager.get_session() as session:
            sample_size = min(100, raw_count)
            raw_data_items = session.query(RawData).limit(sample_size).all()
            print(f"   📝 Processing {len(raw_data_items)} items...")
        
        # Extract ideas using hybrid approach
        ideas = extractor.extract_ideas_from_raw_data(raw_data_items)
        print(f"   💡 Generated {len(ideas)} ideas")
        
        # Save ideas
        saved_count = extractor.save_extracted_ideas(ideas)
        print(f"   💾 Saved {saved_count} ideas to database")
        print("✅ AI Processing and Cross-Paper Analysis complete")
        print()
        
        # Step 2: Idea Generation (additional ideas)
        print("3️⃣ Generating Additional Ideas...")
        print("   🔄 Running cross-paper analysis for additional ideas...")
        
        # Generate more ideas using cross-paper analysis
        additional_ideas = []
        for i in range(0, len(raw_data_items), 10):  # Process in batches
            batch = raw_data_items[i:i+10]
            batch_ideas = extractor._generate_fallback_synthetic_ideas(batch)
            additional_ideas.extend(batch_ideas)
            print(f"   📊 Batch {i//10 + 1}: Generated {len(batch_ideas)} ideas")
        
        # Save additional ideas
        if additional_ideas:
            saved_additional = extractor.save_extracted_ideas(additional_ideas)
            print(f"   💾 Saved {saved_additional} additional ideas")
        
        total_ideas = saved_count + (saved_additional if additional_ideas else 0)
        print(f"✅ Total ideas generated: {total_ideas}")
        print()
        
        # Step 3: Evaluation
        print("4️⃣ Evaluating Ideas...")
        print("   🔄 Running comprehensive evaluation...")
        
        evaluation_results = evaluator.evaluate_all_ideas()
        print(f"   📊 Evaluated {evaluation_results['evaluated']} ideas")
        print(f"   🏆 Found {evaluation_results.get('top_ideas_count', 0)} top ideas")
        print("✅ Evaluation complete")
        print()
        
        # Step 4: Display Results
        print("5️⃣ Results Summary...")
        from storage.models import ExtractedIdea, IdeaEvaluation
        with db_manager.get_session() as session:
            final_idea_count = session.query(ExtractedIdea).count()
            final_evaluation_count = session.query(IdeaEvaluation).count()
        
        print(f"   📊 Total ideas in database: {final_idea_count}")
        print(f"   📊 Total evaluations: {final_evaluation_count}")
        
        # Get top ideas
        top_ideas = evaluator.get_top_ideas(limit=5)
        if top_ideas:
            print("   🏆 Top 5 Ideas:")
            for i, idea in enumerate(top_ideas, 1):
                score = idea.get('overall_score', 0)
                print(f"      {i}. {idea['title'][:60]}... (Score: {score:.2f})")
        
        print()
        print("🎉 Full extraction completed successfully!")
        print(f"⏰ Completed at: {datetime.now().strftime('%H:%M:%S')}")
        print()
        print("💡 Next steps:")
        print("   1. Open the frontend: http://localhost:8000/web_interface/index.html")
        print("   2. Click 'Load Top 50 Ideas' to see the results")
        print("   3. Use pagination to explore all generated ideas")
        
        return True
        
    except Exception as e:
        logger.error(f"Full extraction failed: {e}")
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
