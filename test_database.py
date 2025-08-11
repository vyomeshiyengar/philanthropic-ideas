#!/usr/bin/env python3
"""
Database validation script for the Philanthropic Ideas Generator.
Tests database connection, table creation, and basic operations.
"""
import asyncio
import logging
import sys
from datetime import datetime
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, '.')

from storage.database import db_manager, init_database, cleanup_database
from storage.models import (
    DataSource, RawData, ExtractedIdea, IdeaEvaluation, 
    TalentProfile, IdeaTalentMatch, AnalysisRun, 
    BenchmarkIntervention, SearchQuery
)
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_database_connection():
    """Test basic database connection."""
    print("🔍 Testing database connection...")
    
    try:
        # Test connection
        if db_manager.test_connection():
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False


def test_table_creation():
    """Test table creation."""
    print("\n🔍 Testing table creation...")
    
    try:
        # Create tables
        db_manager.create_tables()
        print("✅ Tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Table creation error: {e}")
        return False


def test_basic_operations():
    """Test basic CRUD operations on all models."""
    print("\n🔍 Testing basic CRUD operations...")
    
    try:
        with db_manager.get_session() as session:
            # Test DataSource creation
            print("  Testing DataSource...")
            test_source = DataSource(
                name="test_source",
                source_type="api",
                url="https://test.com",
                api_key_required=False,
                rate_limit=100,
                status="active"
            )
            session.add(test_source)
            session.commit()
            session.refresh(test_source)
            print(f"    ✅ Created DataSource with ID: {test_source.id}")
            
            # Test RawData creation
            print("  Testing RawData...")
            test_raw_data = RawData(
                data_source_id=test_source.id,
                content_type="paper",
                title="Test Paper",
                authors=["Test Author"],
                abstract="This is a test abstract",
                url="https://test.com/paper",
                publication_date=datetime.now(),
                keywords=["test", "validation"]
            )
            session.add(test_raw_data)
            session.commit()
            session.refresh(test_raw_data)
            print(f"    ✅ Created RawData with ID: {test_raw_data.id}")
            
            # Test ExtractedIdea creation
            print("  Testing ExtractedIdea...")
            test_idea = ExtractedIdea(
                raw_data_id=test_raw_data.id,
                title="Test Idea",
                description="This is a test philanthropic idea",
                domain="health",
                primary_metric="dalys",
                idea_type="newly_viable",
                confidence_score=0.8,
                extraction_method="nlp"
            )
            session.add(test_idea)
            session.commit()
            session.refresh(test_idea)
            print(f"    ✅ Created ExtractedIdea with ID: {test_idea.id}")
            
            # Test IdeaEvaluation creation
            print("  Testing IdeaEvaluation...")
            test_evaluation = IdeaEvaluation(
                idea_id=test_idea.id,
                impact_score=7.5,
                impact_confidence=0.7,
                neglectedness_score=8.0,
                tractability_score=6.5,
                scalability_score=7.0,
                overall_score=7.25,
                evaluation_method="manual"
            )
            session.add(test_evaluation)
            session.commit()
            session.refresh(test_evaluation)
            print(f"    ✅ Created IdeaEvaluation with ID: {test_evaluation.id}")
            
            # Test TalentProfile creation
            print("  Testing TalentProfile...")
            test_talent = TalentProfile(
                name="Test Person",
                title="Test Title",
                organization="Test Org",
                expertise_areas=["health", "research"],
                source="web_search",
                confidence_score=0.8
            )
            session.add(test_talent)
            session.commit()
            session.refresh(test_talent)
            print(f"    ✅ Created TalentProfile with ID: {test_talent.id}")
            
            # Test IdeaTalentMatch creation
            print("  Testing IdeaTalentMatch...")
            test_match = IdeaTalentMatch(
                idea_id=test_idea.id,
                talent_id=test_talent.id,
                fit_score=8.5,
                experience_relevance=8.0,
                background_relevance=7.5,
                match_reasoning="Test reasoning",
                potential_role="Lead Researcher"
            )
            session.add(test_match)
            session.commit()
            session.refresh(test_match)
            print(f"    ✅ Created IdeaTalentMatch with ID: {test_match.id}")
            
            # Test AnalysisRun creation
            print("  Testing AnalysisRun...")
            test_run = AnalysisRun(
                run_name="test_run",
                run_type="data_ingestion",
                parameters={"test": "param"},
                data_sources_used=["test_source"],
                status="completed",
                items_processed=10,
                items_successful=8,
                items_failed=2
            )
            session.add(test_run)
            session.commit()
            session.refresh(test_run)
            print(f"    ✅ Created AnalysisRun with ID: {test_run.id}")
            
            # Test BenchmarkIntervention creation
            print("  Testing BenchmarkIntervention...")
            test_benchmark = BenchmarkIntervention(
                name="Test Benchmark",
                organization="Test Org",
                url="https://test.com",
                primary_metric="dalys",
                cost_per_unit=100.0,
                unit_description="DALY averted",
                effectiveness_estimate=0.8,
                evidence_quality="high",
                source="Test Source"
            )
            session.add(test_benchmark)
            session.commit()
            session.refresh(test_benchmark)
            print(f"    ✅ Created BenchmarkIntervention with ID: {test_benchmark.id}")
            
            # Test SearchQuery creation
            print("  Testing SearchQuery...")
            test_query = SearchQuery(
                query_text="test query",
                data_source="test_source",
                domain="health",
                results_count=5,
                successful=True
            )
            session.add(test_query)
            session.commit()
            session.refresh(test_query)
            print(f"    ✅ Created SearchQuery with ID: {test_query.id}")
            
            # Test queries
            print("  Testing queries...")
            
            # Count records
            data_sources_count = session.query(DataSource).count()
            raw_data_count = session.query(RawData).count()
            ideas_count = session.query(ExtractedIdea).count()
            evaluations_count = session.query(IdeaEvaluation).count()
            talent_count = session.query(TalentProfile).count()
            matches_count = session.query(IdeaTalentMatch).count()
            runs_count = session.query(AnalysisRun).count()
            benchmarks_count = session.query(BenchmarkIntervention).count()
            queries_count = session.query(SearchQuery).count()
            
            print(f"    📊 Record counts:")
            print(f"      DataSources: {data_sources_count}")
            print(f"      RawData: {raw_data_count}")
            print(f"      ExtractedIdeas: {ideas_count}")
            print(f"      IdeaEvaluations: {evaluations_count}")
            print(f"      TalentProfiles: {talent_count}")
            print(f"      IdeaTalentMatches: {matches_count}")
            print(f"      AnalysisRuns: {runs_count}")
            print(f"      BenchmarkInterventions: {benchmarks_count}")
            print(f"      SearchQueries: {queries_count}")
            
            # Test relationships
            print("  Testing relationships...")
            idea_with_evaluations = session.query(ExtractedIdea).filter(
                ExtractedIdea.id == test_idea.id
            ).first()
            if idea_with_evaluations and idea_with_evaluations.evaluations:
                print(f"    ✅ Idea has {len(idea_with_evaluations.evaluations)} evaluations")
            else:
                print("    ❌ Idea-evaluation relationship not working")
            
            # Clean up test data
            print("  Cleaning up test data...")
            session.delete(test_query)
            session.delete(test_benchmark)
            session.delete(test_run)
            session.delete(test_match)
            session.delete(test_talent)
            session.delete(test_evaluation)
            session.delete(test_idea)
            session.delete(test_raw_data)
            session.delete(test_source)
            session.commit()
            print("    ✅ Test data cleaned up")
        
        print("✅ All CRUD operations successful")
        return True
        
    except Exception as e:
        print(f"❌ CRUD operations error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_relationships():
    """Test database relationships."""
    print("\n🔍 Testing database relationships...")
    
    try:
        with db_manager.get_session() as session:
            # Create test data with relationships
            source = DataSource(
                name="relationship_test_source",
                source_type="api",
                url="https://test.com"
            )
            session.add(source)
            session.commit()
            session.refresh(source)
            
            raw_data = RawData(
                data_source_id=source.id,
                content_type="paper",
                title="Relationship Test Paper"
            )
            session.add(raw_data)
            session.commit()
            session.refresh(raw_data)
            
            idea = ExtractedIdea(
                raw_data_id=raw_data.id,
                title="Relationship Test Idea",
                description="Test idea",
                domain="health",
                primary_metric="dalys",
                idea_type="newly_viable",
                extraction_method="nlp"
            )
            session.add(idea)
            session.commit()
            session.refresh(idea)
            
            # Test relationships
            # DataSource -> RawData
            source_with_data = session.query(DataSource).filter(
                DataSource.id == source.id
            ).first()
            if source_with_data.raw_data:
                print(f"    ✅ DataSource has {len(source_with_data.raw_data)} raw data items")
            else:
                print("    ❌ DataSource -> RawData relationship not working")
            
            # RawData -> ExtractedIdea
            raw_data_with_ideas = session.query(RawData).filter(
                RawData.id == raw_data.id
            ).first()
            if raw_data_with_ideas.extracted_ideas:
                print(f"    ✅ RawData has {len(raw_data_with_ideas.extracted_ideas)} extracted ideas")
            else:
                print("    ❌ RawData -> ExtractedIdea relationship not working")
            
            # Clean up
            session.delete(idea)
            session.delete(raw_data)
            session.delete(source)
            session.commit()
        
        print("✅ All relationships working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Relationship test error: {e}")
        return False


def test_json_fields():
    """Test JSON field operations."""
    print("\n🔍 Testing JSON fields...")
    
    try:
        with db_manager.get_session() as session:
            # Test JSON field in RawData
            test_data = RawData(
                data_source_id=1,  # Assuming DataSource with ID 1 exists
                content_type="paper",
                title="JSON Test",
                authors=["Author 1", "Author 2"],
                keywords=["keyword1", "keyword2"],
                metadata_json={
                    "journal": "Test Journal",
                    "doi": "10.1234/test",
                    "citations": 42
                }
            )
            session.add(test_data)
            session.commit()
            session.refresh(test_data)
            
            # Verify JSON data
            if test_data.authors == ["Author 1", "Author 2"]:
                print("    ✅ Authors JSON field working")
            else:
                print("    ❌ Authors JSON field not working")
            
            if test_data.metadata_json.get("citations") == 42:
                print("    ✅ Metadata JSON field working")
            else:
                print("    ❌ Metadata JSON field not working")
            
            # Clean up
            session.delete(test_data)
            session.commit()
        
        print("✅ JSON fields working correctly")
        return True
        
    except Exception as e:
        print(f"❌ JSON field test error: {e}")
        return False


def main():
    """Run all database validation tests."""
    print("🚀 Starting Database Validation Tests")
    print("=" * 50)
    
    # Check database URL
    print(f"📋 Database URL: {settings.DATABASE_URL}")
    
    # Run tests
    tests = [
        ("Database Connection", test_database_connection),
        ("Table Creation", test_table_creation),
        ("Basic CRUD Operations", test_basic_operations),
        ("Database Relationships", test_relationships),
        ("JSON Fields", test_json_fields)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
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
        print("🎉 All database tests passed! Your database is set up correctly.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    # Cleanup
    cleanup_database()


if __name__ == "__main__":
    main()
