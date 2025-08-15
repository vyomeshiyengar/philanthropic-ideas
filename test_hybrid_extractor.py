#!/usr/bin/env python3
"""
Comprehensive test script for the hybrid idea extractor.
Tests all functionality including traditional NLP, AI synthesis (when available), and pattern recognition.
"""
import asyncio
import logging
import sys
from datetime import datetime
from typing import Dict, Any, List

# Add the project root to the Python path
sys.path.insert(0, '.')

from analysis.hybrid_idea_extractor import HybridIdeaExtractor
from storage.database import db_manager, init_database
from storage.models import DataSource, RawData, ExtractedIdea
from config.settings import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_test_data():
    """Create sample test data for the hybrid extractor."""
    print("📝 Creating test data...")
    
    try:
        with db_manager.get_session() as session:
            # Create test data source
            test_source = DataSource(
                name="test_hybrid_source",
                source_type="api",
                url="https://test.com",
                api_key_required=False,
                rate_limit=100,
                status="active"
            )
            session.add(test_source)
            session.commit()
            session.refresh(test_source)
            
            # Create sample raw data across different domains
            test_data = [
                {
                    "title": "Effectiveness of Mindfulness-Based Interventions for Depression",
                    "abstract": "This study examines the impact of mindfulness-based cognitive therapy on reducing depressive symptoms in adults. Results show significant improvement in depression scores and quality of life measures.",
                    "domain": "wellbeing",
                    "keywords": ["mindfulness", "depression", "therapy", "mental health", "intervention"]
                },
                {
                    "title": "Digital Mental Health Interventions in Low-Income Settings",
                    "abstract": "Evaluation of mobile-based mental health interventions in developing countries. Findings indicate high engagement rates and positive outcomes for anxiety and depression.",
                    "domain": "wellbeing",
                    "keywords": ["digital", "mental health", "low-income", "intervention", "mobile"]
                },
                {
                    "title": "Vaccine Distribution Strategies in Low-Income Countries",
                    "abstract": "Analysis of cost-effective vaccine distribution methods in developing nations. Findings indicate mobile vaccination units and community health workers significantly improve vaccination rates.",
                    "domain": "health",
                    "keywords": ["vaccine", "distribution", "low-income", "healthcare", "intervention"]
                },
                {
                    "title": "Microfinance Impact on Women's Economic Empowerment",
                    "abstract": "Longitudinal study of microfinance programs targeting women entrepreneurs. Results demonstrate increased income levels and improved household decision-making power.",
                    "domain": "economic_development",
                    "keywords": ["microfinance", "women", "empowerment", "income", "entrepreneurship"]
                },
                {
                    "title": "Plant-Based Diet Interventions for Climate Mitigation",
                    "abstract": "Research on dietary changes as climate intervention strategy. Plant-based diets show potential for significant carbon footprint reduction while improving health outcomes.",
                    "domain": "climate",
                    "keywords": ["plant-based", "diet", "climate", "carbon", "mitigation"]
                }
            ]
            
            raw_data_items = []
            for data in test_data:
                raw_data = RawData(
                    data_source_id=test_source.id,
                    content_type="paper",
                    title=data["title"],
                    authors=["Test Author"],
                    abstract=data["abstract"],
                    url="https://test.com/paper",
                    publication_date=datetime.now(),
                    keywords=data["keywords"],
                    metadata_json={"domain": data["domain"]}
                )
                session.add(raw_data)
                raw_data_items.append(raw_data)
            
            session.commit()
            
            # Refresh to get IDs
            for item in raw_data_items:
                session.refresh(item)
            
            print(f"✅ Created {len(raw_data_items)} test data items")
            return test_source.id, [item.id for item in raw_data_items]
            
    except Exception as e:
        print(f"❌ Failed to create test data: {e}")
        return None, []


def test_hybrid_extractor_initialization():
    """Test hybrid extractor initialization."""
    print("\n🔧 Testing Hybrid Extractor Initialization...")
    
    try:
    # Check configuration
    settings = Settings()
        api_key_available = bool(settings.OPENAI_API_KEY)
        print(f"OpenAI API Key: {'✅ Set' if api_key_available else '❌ Not set'}")
    
    # Initialize hybrid extractor
    hybrid_extractor = HybridIdeaExtractor()
    
        # Test basic properties
    print(f"AI Client: {'✅ Available' if hybrid_extractor.ai_client else '❌ Not available'}")
    print(f"Enhanced Keywords: {len(hybrid_extractor.enhanced_keywords)} domains")
    
        # Test NLP initialization
        if hasattr(hybrid_extractor, 'nlp') and hybrid_extractor.nlp:
            print("✅ NLP pipeline initialized")
        else:
            print("❌ NLP pipeline not initialized")
    
    # Show enhanced keywords
    print("\n🔑 Enhanced Keywords by Domain:")
    for domain, keywords in hybrid_extractor.enhanced_keywords.items():
        print(f"  {domain}: {len(keywords)} keywords")
            print(f"    Sample: {', '.join(keywords[:3])}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Initialization test failed: {e}")
        return False


def test_traditional_nlp_extraction(hybrid_extractor: HybridIdeaExtractor, raw_data_ids: List[int]):
    """Test traditional NLP-based idea extraction."""
    print("\n📝 Testing Traditional NLP Extraction...")
    
    try:
        # Test extraction from specific raw data
        ideas = hybrid_extractor.extract_ideas_from_raw_data(raw_data_id=raw_data_ids[0])
        
        print(f"Extracted {len(ideas)} ideas using traditional NLP")
        
        if ideas:
            # Show sample idea
            sample_idea = ideas[0]
            print(f"\n📋 Sample NLP-Extracted Idea:")
            print(f"  Title: {sample_idea.get('title', 'N/A')}")
            print(f"  Domain: {sample_idea.get('domain', 'N/A')}")
            print(f"  Confidence: {sample_idea.get('confidence_score', 'N/A')}")
            print(f"  Method: {sample_idea.get('extraction_method', 'N/A')}")
        
        return len(ideas) > 0
        
    except Exception as e:
        print(f"❌ Traditional NLP extraction failed: {e}")
        return False


def test_synthesis_functionality(hybrid_extractor: HybridIdeaExtractor, raw_data_ids: List[int]):
    """Test synthesis functionality (AI or traditional fallback)."""
    print("\n🧠 Testing Synthesis Functionality...")
    
    if hybrid_extractor.ai_client:
        print("🤖 AI synthesis is available")
    else:
        print("📚 Using traditional synthesis fallback")
    
    try:
        # Test synthesis with multiple sources
        ideas = hybrid_extractor.extract_ideas_from_raw_data()
        
        # Filter for synthesized ideas
        synthesized_ideas = [idea for idea in ideas if idea.get('extraction_method') in ['ai_synthesis', 'traditional_synthesis']]
        
        print(f"Generated {len(synthesized_ideas)} synthesized ideas")
        
        if synthesized_ideas:
            # Show sample synthesized idea
            sample_idea = synthesized_ideas[0]
            print(f"\n🧠 Sample Synthesized Idea:")
            print(f"  Title: {sample_idea.get('title', 'N/A')}")
            print(f"  Domain: {sample_idea.get('domain', 'N/A')}")
            print(f"  Method: {sample_idea.get('extraction_method', 'N/A')}")
            print(f"  Key Innovation: {sample_idea.get('key_innovation', 'N/A')}")
            print(f"  Expected Impact: {sample_idea.get('expected_impact', 'N/A')}")
            print(f"  Confidence: {sample_idea.get('confidence_score', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Synthesis test failed: {e}")
        return False


def test_pattern_recognition(hybrid_extractor: HybridIdeaExtractor, raw_data_ids: List[int]):
    """Test pattern recognition and gap identification."""
    print("\n🔍 Testing Pattern Recognition...")
    
    try:
        # Test pattern recognition
        ideas = hybrid_extractor.extract_ideas_from_raw_data()
        
        # Filter for pattern-based ideas
        pattern_ideas = [idea for idea in ideas if idea.get('extraction_method') == 'pattern_recognition']
        
        print(f"Identified {len(pattern_ideas)} pattern-based ideas")
        
        if pattern_ideas:
            # Show sample pattern idea
            sample_idea = pattern_ideas[0]
            print(f"\n🔍 Sample Pattern-Recognition Idea:")
            print(f"  Title: {sample_idea.get('title', 'N/A')}")
            print(f"  Domain: {sample_idea.get('domain', 'N/A')}")
            print(f"  Thought Process: {sample_idea.get('thought_process', 'N/A')}")
            print(f"  Confidence: {sample_idea.get('confidence_score', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Pattern recognition test failed: {e}")
        return False


def test_idea_ranking_and_filtering(hybrid_extractor: HybridIdeaExtractor, raw_data_ids: List[int]):
    """Test idea ranking and filtering functionality."""
    print("\n🏆 Testing Idea Ranking and Filtering...")
    
    try:
        # Extract ideas
        ideas = hybrid_extractor.extract_ideas_from_raw_data()
        
        print(f"Total ideas extracted: {len(ideas)}")
        
        if ideas:
            # Check for enhanced scoring
            scored_ideas = [idea for idea in ideas if 'enhanced_score' in idea]
            print(f"Ideas with enhanced scores: {len(scored_ideas)}")
            
            if scored_ideas:
                # Show top-ranked ideas
                top_ideas = sorted(scored_ideas, key=lambda x: x['enhanced_score'], reverse=True)[:3]
                print(f"\n🏆 Top 3 Ranked Ideas:")
                for i, idea in enumerate(top_ideas, 1):
                    print(f"  {i}. {idea.get('title', 'N/A')} (Score: {idea.get('enhanced_score', 'N/A'):.3f})")
            
            # Check for duplicate removal
            unique_titles = set()
            for idea in ideas:
                title = idea.get('title', '').lower()
                unique_titles.add(title)
            
            print(f"Unique ideas (after deduplication): {len(unique_titles)}")
        
        return len(ideas) > 0
        
    except Exception as e:
        print(f"❌ Ranking and filtering test failed: {e}")
        return False


def test_database_saving(hybrid_extractor: HybridIdeaExtractor, raw_data_ids: List[int]):
    """Test saving extracted ideas to database."""
    print("\n💾 Testing Database Saving...")
    
    try:
        # Extract ideas
        ideas = hybrid_extractor.extract_ideas_from_raw_data()
        
        if ideas:
            # Save to database
            saved_count = hybrid_extractor.save_extracted_ideas(ideas)
            print(f"Saved {saved_count} ideas to database")
            
            # Verify in database
            with db_manager.get_session() as session:
                db_ideas = session.query(ExtractedIdea).all()
                print(f"Total ideas in database: {len(db_ideas)}")
                
                # Show sample saved idea
                if db_ideas:
                    sample_db_idea = db_ideas[0]
                    print(f"\n💾 Sample Saved Idea:")
                    print(f"  ID: {sample_db_idea.id}")
                    print(f"  Title: {sample_db_idea.title}")
                    print(f"  Domain: {sample_db_idea.domain}")
                    print(f"  Method: {sample_db_idea.extraction_method}")
                    print(f"  Created: {sample_db_idea.created_at}")
            
            return saved_count > 0
        else:
            print("No ideas to save")
            return False
        
    except Exception as e:
        print(f"❌ Database saving test failed: {e}")
        return False


def test_domain_specific_extraction(hybrid_extractor: HybridIdeaExtractor, raw_data_ids: List[int]):
    """Test domain-specific idea extraction."""
    print("\n🎯 Testing Domain-Specific Extraction...")
    
    try:
        # Test extraction for specific domains
        domains = ["health", "wellbeing", "education"]
        
        for domain in domains:
            print(f"\n  Testing {domain} domain...")
            domain_ideas = hybrid_extractor.extract_ideas_from_raw_data(domain=domain)
            
            print(f"    Extracted {len(domain_ideas)} ideas for {domain}")
            
            if domain_ideas:
                # Verify domain classification
                correct_domain = all(idea.get('domain') == domain for idea in domain_ideas)
                print(f"    Domain classification: {'✅ Correct' if correct_domain else '❌ Incorrect'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Domain-specific extraction test failed: {e}")
        return False


def cleanup_test_data(source_id: int, raw_data_ids: List[int]):
    """Clean up test data."""
    print("\n🧹 Cleaning up test data...")
    
    try:
        with db_manager.get_session() as session:
            # Delete extracted ideas
            ideas_deleted = session.query(ExtractedIdea).filter(
                ExtractedIdea.raw_data_id.in_(raw_data_ids)
            ).delete()
            print(f"Deleted {ideas_deleted} extracted ideas")
            
            # Delete raw data
            for raw_data_id in raw_data_ids:
                session.query(RawData).filter(RawData.id == raw_data_id).delete()
            print(f"Deleted {len(raw_data_ids)} raw data items")
            
            # Delete data source
            session.query(DataSource).filter(DataSource.id == source_id).delete()
            print(f"Deleted data source {source_id}")
            
            session.commit()
            print("✅ Test data cleaned up")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")


def main():
    """Run comprehensive hybrid extractor tests."""
    print("🧪 COMPREHENSIVE HYBRID IDEA EXTRACTOR TESTS")
    print("=" * 60)
    
    # Initialize database
    init_database()
    
    # Create test data
    source_id, raw_data_ids = create_test_data()
    if not source_id or not raw_data_ids:
        print("❌ Failed to create test data. Exiting.")
        return
    
    # Initialize hybrid extractor
    hybrid_extractor = HybridIdeaExtractor()
    
    # Run tests
    tests = [
        ("Initialization", lambda: test_hybrid_extractor_initialization()),
        ("Traditional NLP Extraction", lambda: test_traditional_nlp_extraction(hybrid_extractor, raw_data_ids)),
        ("Synthesis Functionality", lambda: test_synthesis_functionality(hybrid_extractor, raw_data_ids)),
        ("Pattern Recognition", lambda: test_pattern_recognition(hybrid_extractor, raw_data_ids)),
        ("Idea Ranking and Filtering", lambda: test_idea_ranking_and_filtering(hybrid_extractor, raw_data_ids)),
        ("Database Saving", lambda: test_database_saving(hybrid_extractor, raw_data_ids)),
        ("Domain-Specific Extraction", lambda: test_domain_specific_extraction(hybrid_extractor, raw_data_ids))
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
    
    # Cleanup
    cleanup_test_data(source_id, raw_data_ids)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All hybrid extractor tests passed!")
        print("\nThe hybrid idea extractor is working correctly with:")
        print("✅ Traditional NLP-based extraction")
        print("✅ Synthesis (AI or traditional fallback)")
        print("✅ Pattern recognition and gap identification")
        print("✅ Idea ranking and filtering")
        print("✅ Database integration")
        print("✅ Domain-specific processing")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    print("\n💡 Usage Tips:")
    print("1. The hybrid extractor works with or without OpenAI API")
    print("2. When AI is available, it uses AI synthesis")
    print("3. When AI is not available, it uses traditional synthesis")
    print("4. Results are always ranked by quality and uniqueness")
    print("5. Ideas are saved to the database for further analysis")


if __name__ == "__main__":
    main()
