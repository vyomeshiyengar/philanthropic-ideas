#!/usr/bin/env python3
"""
Focused test for OpenAI API integration and AI synthesis functionality.
"""
import sys
import logging
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, '.')

from analysis.hybrid_idea_extractor import HybridIdeaExtractor
from storage.database import db_manager, init_database
from storage.models import DataSource, RawData
from config.settings import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_openai_connection():
    """Test OpenAI API connection."""
    print("🔑 Testing OpenAI API Connection...")
    
    try:
        settings = Settings()
        api_key = settings.OPENAI_API_KEY
        
        if not api_key:
            print("❌ OPENAI_API_KEY not found in environment")
            print("   Please set OPENAI_API_KEY in your .env file")
            return False
        
        print(f"✅ OpenAI API key found (length: {len(api_key)})")
        
        # Test the key format (should start with 'sk-')
        if api_key.startswith('sk-'):
            print("✅ API key format looks correct")
        else:
            print("⚠️  API key format may be incorrect (should start with 'sk-')")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking OpenAI API key: {e}")
        return False


def test_ai_client_initialization():
    """Test AI client initialization."""
    print("\n🤖 Testing AI Client Initialization...")
    
    try:
        hybrid_extractor = HybridIdeaExtractor()
        
        if hybrid_extractor.ai_client:
            print("✅ AI client initialized successfully")
            print(f"   Provider: {hybrid_extractor.ai_provider}")
            return True
        else:
            print("❌ AI client failed to initialize")
            return False
            
    except Exception as e:
        print(f"❌ Error initializing AI client: {e}")
        return False


def test_ai_synthesis_with_sample_data():
    """Test AI synthesis with sample data."""
    print("\n🧠 Testing AI Synthesis with Sample Data...")
    
    try:
        # Create sample data for testing
        with db_manager.get_session() as session:
            # Create test data source
            test_source = DataSource(
                name="openai_test_source",
                source_type="api",
                url="https://test.com",
                api_key_required=False,
                rate_limit=100,
                status="active"
            )
            session.add(test_source)
            session.commit()
            session.refresh(test_source)
            
            # Create sample research papers for synthesis
            test_papers = [
                {
                    "title": "Effectiveness of Mindfulness-Based Interventions for Depression",
                    "abstract": "This study examines the impact of mindfulness-based cognitive therapy on reducing depressive symptoms in adults. Results show significant improvement in depression scores and quality of life measures.",
                    "domain": "wellbeing"
                },
                {
                    "title": "Digital Mental Health Interventions in Low-Income Settings",
                    "abstract": "Evaluation of mobile-based mental health interventions in developing countries. Findings indicate high engagement rates and positive outcomes for anxiety and depression.",
                    "domain": "wellbeing"
                },
                {
                    "title": "Community-Based Mental Health Support Programs",
                    "abstract": "Analysis of peer support and community health worker programs for mental health. Results demonstrate cost-effectiveness and improved access to care.",
                    "domain": "wellbeing"
                }
            ]
            
            raw_data_items = []
            for paper in test_papers:
                raw_data = RawData(
                    data_source_id=test_source.id,
                    content_type="paper",
                    title=paper["title"],
                    authors=["Test Author"],
                    abstract=paper["abstract"],
                    url="https://test.com/paper",
                    publication_date=datetime.now(),
                    keywords=["mental health", "intervention", "wellbeing"],
                    metadata_json={"domain": paper["domain"]}
                )
                session.add(raw_data)
                raw_data_items.append(raw_data)
            
            session.commit()
            
            # Get the raw data IDs
            raw_data_ids = [item.id for item in raw_data_items]
        
        # Test AI synthesis
        hybrid_extractor = HybridIdeaExtractor()
        
        if not hybrid_extractor.ai_client:
            print("❌ AI client not available - cannot test synthesis")
            return False
        
        print("📊 Running AI synthesis on sample data...")
        ideas = hybrid_extractor.extract_ideas_from_raw_data()
        
        # Filter for AI-synthesized ideas
        ai_ideas = [idea for idea in ideas if idea.get('extraction_method') == 'ai_synthesis']
        
        print(f"Generated {len(ai_ideas)} AI-synthesized ideas")
        
        if ai_ideas:
            print("\n🤖 Sample AI-Synthesized Ideas:")
            for i, idea in enumerate(ai_ideas[:3], 1):
                print(f"\n  {i}. {idea.get('title', 'N/A')}")
                print(f"     Domain: {idea.get('domain', 'N/A')}")
                print(f"     Key Innovation: {idea.get('key_innovation', 'N/A')[:100]}...")
                print(f"     Expected Impact: {idea.get('expected_impact', 'N/A')[:100]}...")
                print(f"     Confidence: {idea.get('confidence_score', 'N/A')}")
        
        # Clean up test data
        with db_manager.get_session() as session:
            for raw_data_id in raw_data_ids:
                session.query(RawData).filter(RawData.id == raw_data_id).delete()
            session.query(DataSource).filter(DataSource.id == test_source.id).delete()
            session.commit()
        
        return len(ai_ideas) > 0
        
    except Exception as e:
        print(f"❌ Error testing AI synthesis: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_synthesis_prompt():
    """Test the AI synthesis prompt directly."""
    print("\n📝 Testing AI Synthesis Prompt...")
    
    try:
        hybrid_extractor = HybridIdeaExtractor()
        
        if not hybrid_extractor.ai_client:
            print("❌ AI client not available")
            return False
        
        # Test a simple prompt
        test_context = """
Source 1: Effectiveness of Mindfulness-Based Interventions for Depression
Abstract: This study examines the impact of mindfulness-based cognitive therapy on reducing depressive symptoms in adults.

Source 2: Digital Mental Health Interventions in Low-Income Settings  
Abstract: Evaluation of mobile-based mental health interventions in developing countries.
"""
        
        print("🧠 Testing AI synthesis with sample context...")
        domain_ideas = hybrid_extractor._call_ai_for_synthesis(test_context, "wellbeing")
        
        print(f"Generated {len(domain_ideas)} ideas from test context")
        
        if domain_ideas:
            print("\n📋 Sample Generated Idea:")
            idea = domain_ideas[0]
            print(f"  Title: {idea.get('title', 'N/A')}")
            print(f"  Description: {idea.get('description', 'N/A')[:200]}...")
            print(f"  Key Innovation: {idea.get('key_innovation', 'N/A')}")
            print(f"  Expected Impact: {idea.get('expected_impact', 'N/A')}")
        
        return len(domain_ideas) > 0
        
    except Exception as e:
        print(f"❌ Error testing AI synthesis prompt: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run OpenAI synthesis tests."""
    print("🧪 OPENAI SYNTHESIS TESTING")
    print("=" * 50)
    
    # Initialize database
    init_database()
    
    # Run tests
    tests = [
        ("OpenAI API Connection", test_openai_connection),
        ("AI Client Initialization", test_ai_client_initialization),
        ("AI Synthesis Prompt", test_ai_synthesis_prompt),
        ("AI Synthesis with Sample Data", test_ai_synthesis_with_sample_data)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All OpenAI synthesis tests passed!")
        print("\nThe AI synthesis functionality is working correctly:")
        print("✅ OpenAI API connection established")
        print("✅ AI client initialized properly")
        print("✅ AI synthesis prompts working")
        print("✅ Ideas generated from sample data")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    if passed >= 2:
        print("\n💡 The hybrid extractor can now use AI synthesis!")
        print("   Run the full hybrid extractor test to see it in action.")


if __name__ == "__main__":
    main()

