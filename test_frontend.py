#!/usr/bin/env python3
"""
Simple script to test the frontend and API without running the pipeline.
"""
import requests
import time

def test_frontend_access():
    """Test if the frontend is accessible and working."""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Frontend Access")
    print("=" * 50)
    
    # Test if server is running
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ API server is running")
        else:
            print(f"❌ API server health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API server: {e}")
        print("💡 Start the server with: python -m api.main")
        return False
    
    # Test frontend page
    try:
        response = requests.get(f"{base_url}/web_interface/index.html")
        if response.status_code == 200:
            print("✅ Frontend page is accessible")
        else:
            print(f"❌ Frontend page failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot access frontend: {e}")
    
    # Test API endpoints
    try:
        response = requests.get(f"{base_url}/prototype/status")
        if response.status_code == 200:
            status = response.json()
            print(f"📊 Database Status:")
            print(f"   Total raw data: {status.get('total_raw_data', 0)}")
            print(f"   Total ideas: {status.get('total_ideas', 0)}")
            print(f"   Evaluated ideas: {status.get('evaluated_ideas', 0)}")
        else:
            print(f"❌ Failed to get status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting status: {e}")
    
    # Test top ideas endpoint
    try:
        response = requests.get(f"{base_url}/prototype/top-ideas?limit=3")
        if response.status_code == 200:
            ideas = response.json()
            print(f"\n🏆 Top 3 Ideas Available:")
            for i, idea in enumerate(ideas, 1):
                print(f"   {i}. {idea.get('title', 'N/A')} (Score: {idea.get('overall_score', 'N/A')})")
        else:
            print(f"❌ Failed to get top ideas: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting top ideas: {e}")
    
    print(f"\n🌐 Frontend URL: {base_url}/web_interface/index.html")
    print("💡 Instructions:")
    print("   1. Open the frontend URL in your browser")
    print("   2. Click 'Load Top 10 Ideas' to see the hybrid-generated ideas")
    print("   3. Click 'View Results' then 'Load Ideas' to see all extracted ideas")
    print("   4. NO NEED to click 'Run Pipeline' - ideas are already available!")
    
    return True

if __name__ == "__main__":
    test_frontend_access()
