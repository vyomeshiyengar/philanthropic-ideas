#!/usr/bin/env python3
"""
Installation script for Philanthropic Ideas Generator.
Automatically detects Python version and installs appropriate dependencies.
"""
import sys
import subprocess
import platform
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    print(f"🐍 Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required!")
        return False
    
    if version.major == 3 and version.minor >= 12:
        print("✅ Python 3.12+ detected - will use Python 3.12 compatible requirements")
        return "py312"
    else:
        print("✅ Python version compatible - will use standard requirements")
        return "standard"

def install_dependencies(requirements_file):
    """Install dependencies from the specified requirements file."""
    print(f"\n📦 Installing dependencies from {requirements_file}...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", requirements_file
        ], capture_output=True, text=True, check=True)
        
        print("✅ Dependencies installed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies:")
        print(f"Error: {e.stderr}")
        return False

def install_spacy_model():
    """Install spaCy English model."""
    print("\n📚 Installing spaCy English model...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "spacy", "download", "en_core_web_sm"
        ], capture_output=True, text=True, check=True)
        
        print("✅ spaCy model installed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing spaCy model:")
        print(f"Error: {e.stderr}")
        return False

def download_nltk_data():
    """Download required NLTK data."""
    print("\n📖 Downloading NLTK data...")
    
    try:
        import nltk
        nltk.download('punkt')
        nltk.download('stopwords')
        nltk.download('wordnet')
        print("✅ NLTK data downloaded successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error downloading NLTK data: {e}")
        return False

def main():
    """Main installation function."""
    print("🚀 Philanthropic Ideas Generator - Installation Script")
    print("=" * 60)
    
    # Check Python version
    python_type = check_python_version()
    if not python_type:
        sys.exit(1)
    
    # Determine requirements file
    if python_type == "py312":
        requirements_file = "requirements-py312.txt"
    else:
        requirements_file = "requirements.txt"
    
    # Check if requirements file exists
    if not Path(requirements_file).exists():
        print(f"❌ Requirements file {requirements_file} not found!")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies(requirements_file):
        print("\n💡 Troubleshooting tips:")
        print("1. Make sure you're in a virtual environment")
        print("2. Try upgrading pip: python -m pip install --upgrade pip")
        print("3. For Python 3.12+, try: pip install -r requirements-py312.txt")
        sys.exit(1)
    
    # Install spaCy model
    install_spacy_model()
    
    # Download NLTK data
    download_nltk_data()
    
    print("\n🎉 Installation completed successfully!")
    print("\n📋 Next steps:")
    print("1. Copy env_template.txt to .env and configure your settings")
    print("2. Set up your database (see SETUP_GUIDE.md)")
    print("3. Run the application: python run.py")
    print("\n📚 For more information, see README.md and SETUP_GUIDE.md")

if __name__ == "__main__":
    main()
