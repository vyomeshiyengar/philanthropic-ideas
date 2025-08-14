#!/usr/bin/env python3
"""
Test script to verify API endpoints are returning hybrid-generated ideas.
"""
import requests
import json
import time

def test_api_endpoints():
    """Test the API endpoints to see if they're returning ideas."""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing API Endpoints")
    print("=" * 50)
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ API server is running")
        else:
            print(f"❌ API server health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API server: {e}")
        print("💡 Make sure to start the API server with: python -m api.main")
        return False
    
    # Test prototype status
    try:
        response = requests.get(f"{base_url}/prototype/status")
        if response.status_code == 200:
            status = response.json()
            print(f"📊 Prototype Status:")
            print(f"   Total raw data: {status.get('total_raw_data', 0)}")
            print(f"   Total ideas: {status.get('total_ideas', 0)}")
            print(f"   Evaluated ideas: {status.get('evaluated_ideas', 0)}")
        else:
            print(f"❌ Failed to get prototype status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting prototype status: {e}")
    
    # Test top ideas endpoint
    try:
        response = requests.get(f"{base_url}/prototype/top-ideas?limit=5")
        if response.status_code == 200:
            top_ideas = response.json()
            print(f"\n🏆 Top Ideas (API): {len(top_ideas)} ideas")
            for i, idea in enumerate(top_ideas[:3], 1):
                print(f"   {i}. {idea.get('title', 'N/A')} (Score: {idea.get('overall_score', 'N/A')})")
        else:
            print(f"❌ Failed to get top ideas: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting top ideas: {e}")
    
    # Test extracted ideas endpoint
    try:
        response = requests.get(f"{base_url}/prototype/ideas?limit=5")
        if response.status_code == 200:
            ideas = response.json()
            print(f"\n💡 Extracted Ideas (API): {len(ideas)} ideas")
            for i, idea in enumerate(ideas[:3], 1):
                print(f"   {i}. {idea.get('title', 'N/A')} (Confidence: {idea.get('confidence_score', 'N/A')})")
        else:
            print(f"❌ Failed to get extracted ideas: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting extracted ideas: {e}")
    
    return True

def test_database_directly():
    """Test database directly to compare with API results."""
    print(f"\n🔍 Testing Database Directly")
    print("=" * 50)
    
    try:
        from storage.database import db_manager
        from storage.models import ExtractedIdea, IdeaEvaluation
        from sqlalchemy.orm import Session
        from sqlalchemy import desc
        
        session = Session(db_manager.engine)
        
        # Get total counts
        total_ideas = session.query(ExtractedIdea).count()
        total_evaluations = session.query(IdeaEvaluation).count()
        
        print(f"📊 Database Status:")
        print(f"   Total ideas: {total_ideas}")
        print(f"   Total evaluations: {total_evaluations}")
        
        # Get top evaluated ideas
        top_evaluations = session.query(IdeaEvaluation, ExtractedIdea).join(
            ExtractedIdea, IdeaEvaluation.idea_id == ExtractedIdea.id
        ).order_by(desc(IdeaEvaluation.overall_score)).limit(5).all()
        
        print(f"\n🏆 Top Ideas (Database): {len(top_evaluations)} ideas")
        for i, (evaluation, idea) in enumerate(top_evaluations[:3], 1):
            print(f"   {i}. {idea.title} (Score: {evaluation.overall_score:.2f})")
        
        # Get recent extracted ideas
        recent_ideas = session.query(ExtractedIdea).order_by(
            ExtractedIdea.created_at.desc()
        ).limit(5).all()
        
        print(f"\n💡 Recent Ideas (Database): {len(recent_ideas)} ideas")
        for i, idea in enumerate(recent_ideas[:3], 1):
            print(f"   {i}. {idea.title} (Confidence: {idea.confidence_score:.2f})")
        
        session.close()
        
    except Exception as e:
        print(f"❌ Error testing database: {e}")

def main():
    """Main test function."""
    print("🚀 Testing Hybrid Ideas Display")
    print("=" * 60)
    
    # Test API endpoints
    api_working = test_api_endpoints()
    
    # Test database directly
    test_database_directly()
    
    if api_working:
        print(f"\n🌐 Frontend should be accessible at: http://localhost:8000/web_interface/index.html")
        print("💡 Open the frontend and click 'Load Top 10 Ideas' to see the hybrid-generated ideas")
    else:
        print(f"\n❌ API server is not running. Start it with: python -m api.main")

if __name__ == "__main__":
    main()
