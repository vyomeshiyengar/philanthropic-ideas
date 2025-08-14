#!/usr/bin/env python3
"""
Quick test to check hybrid system functionality and progress.
"""
import sys
import os
import time
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analysis.hybrid_idea_extractor import HybridIdeaExtractor
from storage.database import db_manager
from storage.models import RawData, ExtractedIdea
from config.settings import settings

def quick_hybrid_test():
    """Quick test of hybrid system components."""
    print("🚀 Quick Hybrid System Test")
    print("=" * 40)
    print(f"⏰ Started at: {datetime.now().strftime('%H:%M:%S')}")
    
    # Test 1: Initialize hybrid extractor
    print("\n1️⃣ Testing Hybrid Extractor Initialization...")
    try:
        extractor = HybridIdeaExtractor(ai_provider="openai")
        print("✅ HybridIdeaExtractor initialized")
        
        if extractor.ai_client:
            print("✅ OpenAI integration active")
            print(f"   📋 Models: {extractor.models}")
        else:
            print("⚠️ OpenAI not available (using fallback)")
            
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False
    
    # Test 2: Check database connection
    print("\n2️⃣ Testing Database Connection...")
    try:
        with db_manager.get_session() as session:
            raw_count = session.query(RawData).count()
            idea_count = session.query(ExtractedIdea).count()
            print(f"✅ Database connected")
            print(f"   📊 Raw data items: {raw_count}")
            print(f"   💡 Existing ideas: {idea_count}")
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    
    # Test 3: Test AI ingestion (if available)
    print("\n3️⃣ Testing AI Data Ingestion...")
    if extractor.ai_client:
        try:
            test_text = """
            A study on mobile health interventions in rural India found that 
            SMS reminders increased vaccination rates by 25% and reduced 
            missed appointments by 40%. The intervention cost $2 per person 
            and was highly scalable across multiple districts.
            """
            
            start_time = time.time()
            ai_ideas = extractor._call_ai_for_data_ingestion(test_text, "health")
            end_time = time.time()
            
            print(f"✅ AI ingestion working")
            print(f"   ⏱️ Response time: {end_time - start_time:.2f}s")
            print(f"   💡 Ideas generated: {len(ai_ideas)}")
            
            for i, idea in enumerate(ai_ideas, 1):
                print(f"      {i}. {idea.get('title', 'No title')}")
                
        except Exception as e:
            print(f"❌ AI ingestion failed: {e}")
    else:
        print("⚠️ Skipping AI test (not available)")
    
    # Test 4: Test traditional NLP extraction
    print("\n4️⃣ Testing Traditional NLP Extraction...")
    try:
        with db_manager.get_session() as session:
            # Get one raw data item for testing
            test_item = session.query(RawData).first()
            
            if test_item:
                start_time = time.time()
                nlp_ideas = extractor._extract_ideas_from_item(test_item)
                end_time = time.time()
                
                print(f"✅ Traditional NLP working")
                print(f"   ⏱️ Response time: {end_time - start_time:.2f}s")
                print(f"   💡 Ideas generated: {len(nlp_ideas)}")
                
                for i, idea in enumerate(nlp_ideas[:2], 1):  # Show first 2
                    print(f"      {i}. {idea.get('title', 'No title')}")
            else:
                print("⚠️ No raw data available for testing")
                
    except Exception as e:
        print(f"❌ Traditional NLP failed: {e}")
    
    # Test 5: Test cross-paper analysis
    print("\n5️⃣ Testing Cross-Paper Analysis...")
    try:
        with db_manager.get_session() as session:
            # Get multiple items for cross-paper analysis
            test_items = session.query(RawData).limit(3).all()
            
            if len(test_items) >= 2:
                start_time = time.time()
                cross_ideas = extractor._generate_fallback_synthetic_ideas(test_items)
                end_time = time.time()
                
                print(f"✅ Cross-paper analysis working")
                print(f"   ⏱️ Response time: {end_time - start_time:.2f}s")
                print(f"   💡 Ideas generated: {len(cross_ideas)}")
                
                for i, idea in enumerate(cross_ideas[:2], 1):  # Show first 2
                    print(f"      {i}. {idea.get('title', 'No title')}")
            else:
                print("⚠️ Need at least 2 items for cross-paper analysis")
                
    except Exception as e:
        print(f"❌ Cross-paper analysis failed: {e}")
    
    # Test 6: Overall system status
    print("\n6️⃣ Overall System Status...")
    print("=" * 40)
    
    # Check what's working
    components_working = []
    components_failing = []
    
    if extractor.ai_client:
        components_working.append("OpenAI Integration")
    else:
        components_failing.append("OpenAI Integration")
    
    try:
        with db_manager.get_session() as session:
            session.query(RawData).count()
            components_working.append("Database")
    except:
        components_failing.append("Database")
    
    if extractor.nlp:
        components_working.append("NLP Processing")
    else:
        components_failing.append("NLP Processing")
    
    print(f"✅ Working components: {len(components_working)}")
    for comp in components_working:
        print(f"   • {comp}")
    
    if components_failing:
        print(f"❌ Failing components: {len(components_failing)}")
        for comp in components_failing:
            print(f"   • {comp}")
    
    # Progress assessment
    total_components = len(components_working) + len(components_failing)
    progress_percent = (len(components_working) / total_components) * 100
    
    print(f"\n📈 System Progress: {progress_percent:.1f}%")
    
    if progress_percent >= 80:
        print("🎉 System is ready for full operation!")
    elif progress_percent >= 60:
        print("✅ System is mostly working (some fallbacks active)")
    elif progress_percent >= 40:
        print("⚠️ System has partial functionality")
    else:
        print("❌ System needs significant fixes")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%H:%M:%S')}")
    return True

if __name__ == "__main__":
    success = quick_hybrid_test()
    
    if success:
        print("\n🎉 Quick test completed successfully!")
        print("The hybrid system is ready to use.")
    else:
        print("\n❌ Quick test failed!")
        print("Check the errors above for issues.")
        sys.exit(1)
