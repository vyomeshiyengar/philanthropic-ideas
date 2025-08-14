#!/usr/bin/env python3
"""
Mac Python 3.12 Installation Script
"""
import sys
import subprocess
import os
import platform
from pathlib import Path

def check_mac_system():
    """Check if running on Mac."""
    print("🍎 Mac System Check")
    print("=" * 25)
    
    if platform.system() != "Darwin":
        print("❌ This script is for macOS only")
        return False
    
    print("✅ Running on macOS")
    return True

def check_python_version():
    """Check Python version."""
    print("\n🐍 Python Version Check")
    print("=" * 25)
    
    version = sys.version_info
    print(f"Current: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 12:
        print("✅ Python 3.12+ detected")
        return True
    else:
        print("❌ Python 3.12+ required")
        print("💡 Install with: brew install python@3.12")
        return False

def install_xcode_tools():
    """Install Xcode Command Line Tools."""
    print("\n🔧 Installing Xcode Command Line Tools")
    print("=" * 40)
    
    try:
        result = subprocess.run(["xcode-select", "--print-path"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Xcode Command Line Tools already installed")
            return True
    except FileNotFoundError:
        pass
    
    print("📦 Installing Xcode Command Line Tools...")
    print("This may take several minutes...")
    
    try:
        subprocess.run(["xcode-select", "--install"], check=True)
        print("✅ Xcode Command Line Tools installation initiated")
        print("💡 Please complete the installation in the popup window")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install Xcode Command Line Tools")
        return False

def check_homebrew():
    """Check if Homebrew is installed."""
    print("\n🍺 Homebrew Check")
    print("=" * 20)
    
    try:
        result = subprocess.run(["brew", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Homebrew is installed")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ Homebrew not found")
    print("💡 Install with: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
    return False

def create_virtual_environment():
    """Create virtual environment."""
    print("\n🏗️ Creating Virtual Environment")
    print("=" * 35)
    
    venv_path = Path("venv")
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return True
    
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to create virtual environment")
        return False

def upgrade_pip():
    """Upgrade pip and build tools."""
    print("\n📦 Upgrading Pip and Build Tools")
    print("=" * 35)
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], check=True)
        print("✅ Pip and build tools upgraded")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to upgrade pip")
        return False

def install_requirements():
    """Install requirements."""
    print("\n📦 Installing Requirements")
    print("=" * 25)
    
    # Check if requirements file exists
    requirements_file = "requirements-mac-py312.txt"
    if not Path(requirements_file).exists():
        print(f"❌ {requirements_file} not found")
        print("💡 Run check_mac_compatibility.py first")
        return False
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", requirements_file], check=True)
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def install_spacy_model():
    """Install spaCy model."""
    print("\n🧠 Installing spaCy Model")
    print("=" * 25)
    
    try:
        subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], check=True)
        print("✅ spaCy model installed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install spaCy model")
        return False

def install_nltk_data():
    """Install NLTK data."""
    print("\n📚 Installing NLTK Data")
    print("=" * 25)
    
    nltk_script = """
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
print('NLTK data installed successfully')
"""
    
    try:
        subprocess.run([sys.executable, "-c", nltk_script], check=True)
        print("✅ NLTK data installed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install NLTK data")
        return False

def test_installation():
    """Test the installation."""
    print("\n🧪 Testing Installation")
    print("=" * 25)
    
    test_imports = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "pandas",
        "numpy",
        "spacy",
        "nltk",
        "openai",
        "requests"
    ]
    
    failed_imports = []
    
    for package in test_imports:
        try:
            __import__(package)
            print(f"✅ {package}: OK")
        except ImportError:
            print(f"❌ {package}: Failed")
            failed_imports.append(package)
    
    if failed_imports:
        print(f"\n⚠️ Failed imports: {', '.join(failed_imports)}")
        return False
    else:
        print("\n🎉 All packages imported successfully!")
        return True

def provide_next_steps():
    """Provide next steps."""
    print("\n🎯 Next Steps")
    print("=" * 15)
    
    steps = """
✅ Installation Complete!

Next steps:

1. Activate virtual environment:
   source venv/bin/activate

2. Set up your .env file with API keys:
   cp env_template.txt .env
   # Edit .env with your API keys

3. Initialize the database:
   python -c "from storage.database import db_manager; db_manager.create_tables()"

4. Run the quick test:
   python quick_hybrid_test.py

5. Start the API server:
   python api_server_start.py

6. Open the frontend:
   open web_interface/index.html

For troubleshooting, see MAC_INSTALLATION_GUIDE.md
"""
    
    print(steps)

def main():
    """Main installation process."""
    print("🍎 Mac Python 3.12 Installation Script")
    print("=" * 50)
    
    # Check system
    if not check_mac_system():
        return False
    
    # Check Python version
    if not check_python_version():
        print("\n💡 Please install Python 3.12+ first:")
        print("   brew install python@3.12")
        return False
    
    # Install Xcode tools
    if not install_xcode_tools():
        print("\n💡 Please install Xcode Command Line Tools manually")
        return False
    
    # Check Homebrew
    if not check_homebrew():
        print("\n💡 Please install Homebrew first")
        return False
    
    # Create virtual environment
    if not create_virtual_environment():
        return False
    
    # Upgrade pip
    if not upgrade_pip():
        return False
    
    # Install requirements
    if not install_requirements():
        return False
    
    # Install spaCy model
    if not install_spacy_model():
        return False
    
    # Install NLTK data
    if not install_nltk_data():
        return False
    
    # Test installation
    if not test_installation():
        return False
    
    # Provide next steps
    provide_next_steps()
    
    return True

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎉 Installation completed successfully!")
    else:
        print("\n❌ Installation failed. Check the errors above.")
        sys.exit(1)
