#!/usr/bin/env python3
"""
Mac Python 3.12 Compatibility Checker
"""
import sys
import platform
import subprocess
import importlib
from pathlib import Path

def check_system_info():
    """Check system information."""
    print("🖥️ System Information")
    print("=" * 40)
    print(f"Platform: {platform.platform()}")
    print(f"Python Version: {sys.version}")
    print(f"Architecture: {platform.architecture()}")
    print(f"Machine: {platform.machine()}")
    print(f"Processor: {platform.processor()}")

def check_python_version():
    """Check if Python version is compatible."""
    print("\n🐍 Python Version Check")
    print("=" * 30)
    
    version = sys.version_info
    print(f"Current: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor == 12:
        print("✅ Python 3.12 detected - compatible")
        return True
    elif version.major == 3 and version.minor >= 12:
        print("✅ Python 3.12+ detected - compatible")
        return True
    else:
        print("❌ Python 3.12+ required")
        return False

def check_pip_version():
    """Check pip version."""
    print("\n📦 Pip Version Check")
    print("=" * 25)
    
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                              capture_output=True, text=True)
        print(f"Pip: {result.stdout.strip()}")
        return True
    except Exception as e:
        print(f"❌ Error checking pip: {e}")
        return False

def check_problematic_packages():
    """Check for known problematic packages on Mac Python 3.12."""
    print("\n⚠️ Known Problematic Packages (Mac Python 3.12)")
    print("=" * 55)
    
    problematic_packages = {
        "wordcloud": "Has configparser issues on Python 3.12",
        "psycopg2-binary": "May need psycopg2-binary==2.9.9+",
        "spacy": "May need specific version for Python 3.12",
        "transformers": "May have torch dependency issues",
        "torch": "Platform-specific installation required",
        "selenium": "May need webdriver-manager",
        "matplotlib": "May have backend issues on Mac",
        "scipy": "May need specific version for Python 3.12"
    }
    
    for package, issue in problematic_packages.items():
        print(f"   • {package}: {issue}")

def check_required_tools():
    """Check if required build tools are available."""
    print("\n🔧 Required Build Tools")
    print("=" * 25)
    
    tools = {
        "xcode": "Xcode Command Line Tools",
        "homebrew": "Homebrew package manager",
        "git": "Git version control"
    }
    
    for tool, description in tools.items():
        try:
            result = subprocess.run([tool, "--version"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {description}: Available")
            else:
                print(f"❌ {description}: Not found")
        except FileNotFoundError:
            print(f"❌ {description}: Not found")

def check_package_installation():
    """Test installation of key packages."""
    print("\n🧪 Package Installation Test")
    print("=" * 30)
    
    test_packages = [
        "fastapi",
        "uvicorn", 
        "sqlalchemy",
        "pandas",
        "numpy",
        "requests",
        "openai"
    ]
    
    for package in test_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package}: Already installed")
        except ImportError:
            print(f"❌ {package}: Not installed")

def generate_mac_requirements():
    """Generate Mac-specific requirements file."""
    print("\n📝 Generating Mac Python 3.12 Requirements")
    print("=" * 45)
    
    mac_requirements = """# Mac Python 3.12 Compatible Requirements
# Core dependencies
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
redis==5.0.1

# Build tools (ensure modern build env for wheels)
setuptools>=68.0.0
wheel>=0.41.2

# Data processing and analysis
pandas>=2.2.1
numpy>=1.26.4
scikit-learn>=1.4.0
nltk==3.8.1
spacy>=3.7.4
transformers==4.36.2

# Web scraping and API clients
requests==2.31.0
aiohttp==3.9.1
beautifulsoup4==4.13.4
selenium==4.15.2
feedparser==6.0.11

# Data sources APIs
biopython>=1.83

# Search and talent identification
google-api-python-client==2.108.0

# Configuration and environment
python-dotenv==1.0.0
pydantic-settings==2.1.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2

# Development tools
black==23.11.0
flake8==6.1.0
mypy==1.7.1

# Monitoring and logging
structlog==23.2.0
prometheus-client==0.19.0

# Task queue
celery==5.3.4

# Caching
cachetools==5.3.2

# Date and time
python-dateutil==2.8.2
pytz==2023.3

# JSON and data formats
jsonschema==4.20.0
xmltodict==0.13.0

# Visualization (for analysis)
matplotlib==3.8.2
seaborn==0.13.0
plotly==5.17.0

# Database utilities
asyncpg==0.29.0

# Rate limiting
ratelimit==2.2.1

# Text processing
textblob==0.17.1
# wordcloud==1.9.2  # Removed due to Python 3.12 compatibility issues

# AI Integration
openai>=1.0.0

# Machine learning utilities
scipy>=1.12.0
networkx==3.2.1

# Mac-specific additions
certifi>=2023.7.22
charset-normalizer>=3.3.2
idna>=3.4
urllib3>=2.0.7
"""
    
    with open("requirements-mac-py312.txt", "w", encoding="utf-8") as f:
        f.write(mac_requirements)
    
    print("✅ Generated requirements-mac-py312.txt")

def provide_mac_installation_guide():
    """Provide Mac-specific installation guide."""
    print("\n📋 Mac Python 3.12 Installation Guide")
    print("=" * 45)
    
    guide = """
🔧 Pre-Installation Steps:

1. Install Xcode Command Line Tools:
   xcode-select --install

2. Install Homebrew (if not installed):
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

3. Install Python 3.12:
   brew install python@3.12

4. Create virtual environment:
   python3.12 -m venv venv
   source venv/bin/activate

5. Upgrade pip:
   pip install --upgrade pip setuptools wheel

📦 Installation Steps:

1. Install requirements:
   pip install -r requirements-mac-py312.txt

2. Install spaCy model:
   python -m spacy download en_core_web_sm

3. Install NLTK data:
   python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"

⚠️ Common Mac Issues & Solutions:

1. psycopg2-binary issues:
   brew install postgresql
   pip install psycopg2-binary==2.9.9

2. matplotlib backend issues:
   echo "backend: TkAgg" > ~/.matplotlib/matplotlibrc

3. SSL certificate issues:
   pip install certifi --upgrade

4. Permission issues:
   pip install --user package_name

5. Architecture issues (M1/M2 Macs):
   arch -arm64 pip install package_name
   arch -x86_64 pip install package_name
"""
    
    print(guide)
    
    # Save guide to file
    with open("MAC_INSTALLATION_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(guide)
    
    print("✅ Saved MAC_INSTALLATION_GUIDE.md")

def main():
    """Main compatibility check."""
    print("🍎 Mac Python 3.12 Compatibility Checker")
    print("=" * 50)
    
    # Run all checks
    check_system_info()
    python_ok = check_python_version()
    pip_ok = check_pip_version()
    check_problematic_packages()
    check_required_tools()
    check_package_installation()
    
    # Generate Mac-specific files
    generate_mac_requirements()
    provide_mac_installation_guide()
    
    print("\n🎯 Summary")
    print("=" * 15)
    
    if python_ok and pip_ok:
        print("✅ System appears compatible with Mac Python 3.12")
        print("📝 Use requirements-mac-py312.txt for installation")
        print("📖 Check MAC_INSTALLATION_GUIDE.md for detailed steps")
    else:
        print("❌ System has compatibility issues")
        print("🔧 Follow the installation guide to resolve issues")

if __name__ == "__main__":
    main()
