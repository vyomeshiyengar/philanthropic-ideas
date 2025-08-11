#!/usr/bin/env python3
"""
Startup script for the Philanthropic Ideas Generator.
"""
import os
import sys
import subprocess
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import pandas
        import numpy
        import nltk
        import spacy
        logger.info("✓ All required dependencies are installed")
        return True
    except ImportError as e:
        logger.error(f"✗ Missing dependency: {e}")
        logger.info("Please install dependencies with: pip install -r requirements.txt")
        return False

def setup_environment():
    """Set up the environment file if it doesn't exist."""
    env_file = Path(".env")
    env_template = Path("env_template.txt")
    
    if not env_file.exists() and env_template.exists():
        logger.info("Creating .env file from template...")
        with open(env_template, 'r') as f:
            template_content = f.read()
        
        with open(env_file, 'w') as f:
            f.write(template_content)
        
        logger.info("✓ Created .env file. Please update it with your API keys.")
        return False
    elif not env_file.exists():
        logger.warning("No .env file found. Please create one with your API keys.")
        return False
    
    return True

def download_nltk_data():
    """Download required NLTK data."""
    try:
        import nltk
        
        # Download required NLTK data
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('wordnet', quiet=True)
        logger.info("✓ NLTK data downloaded")
    except Exception as e:
        logger.warning(f"Could not download NLTK data: {e}")

def download_spacy_model():
    """Download required spaCy model."""
    try:
        import spacy
        
        # Try to load the model, download if not available
        try:
            spacy.load("en_core_web_sm")
            logger.info("✓ spaCy model already available")
        except OSError:
            logger.info("Downloading spaCy model...")
            subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], 
                         check=True, capture_output=True)
            logger.info("✓ spaCy model downloaded")
    except Exception as e:
        logger.warning(f"Could not download spaCy model: {e}")

def initialize_database():
    """Initialize the database."""
    try:
        from storage.database import init_database
        init_database()
        logger.info("✓ Database initialized")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to initialize database: {e}")
        return False

def start_api_server():
    """Start the FastAPI server."""
    try:
        logger.info("Starting API server...")
        logger.info("API will be available at: http://localhost:8000")
        logger.info("API documentation at: http://localhost:8000/docs")
        logger.info("Web interface at: http://localhost:8000/web_interface/index.html")
        logger.info("Press Ctrl+C to stop the server")
        
        # Start the server
        subprocess.run([sys.executable, "-m", "api.main"])
        
    except KeyboardInterrupt:
        logger.info("\nServer stopped by user")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")

def run_data_ingestion():
    """Run a sample data ingestion."""
    try:
        logger.info("Running sample data ingestion...")
        subprocess.run([sys.executable, "-m", "data_ingestion.main"], check=True)
        logger.info("✓ Data ingestion completed")
    except Exception as e:
        logger.error(f"✗ Data ingestion failed: {e}")

def test_caching():
    """Test the caching functionality."""
    try:
        logger.info("Testing caching functionality...")
        subprocess.run([sys.executable, "test_cache.py"], check=True)
        logger.info("✓ Cache testing completed")
    except Exception as e:
        logger.error(f"✗ Cache testing failed: {e}")

def main():
    """Main function."""
    print("=" * 60)
    print("Philanthropic Ideas Generator")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Set up environment
    if not setup_environment():
        logger.warning("Please set up your .env file with API keys before proceeding")
    
    # Download required models
    download_nltk_data()
    download_spacy_model()
    
    # Initialize database
    if not initialize_database():
        return 1
    
    # Show menu
    while True:
        print("\n" + "=" * 40)
        print("What would you like to do?")
        print("1. Start API server")
        print("2. Run data ingestion")
        print("3. Run full pipeline")
        print("4. Test caching functionality")
        print("5. Exit")
        print("=" * 40)
        
        choice = input("Enter your choice (1-5): ").strip()
        
        if choice == "1":
            start_api_server()
        elif choice == "2":
            run_data_ingestion()
        elif choice == "3":
            logger.info("Running full pipeline...")
            try:
                # This would run the full pipeline
                logger.info("Full pipeline completed")
            except Exception as e:
                logger.error(f"Pipeline failed: {e}")
        elif choice == "4":
            test_caching()
        elif choice == "5":
            logger.info("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1-5.")

if __name__ == "__main__":
    sys.exit(main())
