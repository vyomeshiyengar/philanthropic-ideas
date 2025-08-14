#!/usr/bin/env python3
"""
Simple script to start the API server.
"""
import uvicorn
from api.main import app

if __name__ == "__main__":
    print("🚀 Starting API server...")
    print("📡 Server will be available at: http://localhost:8000")
    print("🌐 Frontend will be available at: http://localhost:8000/web_interface/index.html")
    print("⏹️  Press Ctrl+C to stop the server")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
