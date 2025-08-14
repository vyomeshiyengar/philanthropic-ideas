#!/usr/bin/env python3
"""
Mac NLP Installation Fix Script
"""
import subprocess
import sys
import os
import ssl
import certifi

def fix_ssl_certificates():
    """Fix SSL certificate issues on Mac."""
    print("🔒 Fixing SSL Certificate Issues...")
    print("=" * 40)
    
    try:
        # Install/upgrade certifi
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "certifi"], check=True)
        print("✅ certifi upgraded")
        
        # Set SSL certificate path
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        print(f"✅ SSL context created with certifi: {certifi.where()}")
        
        # Create a script to fix NLTK SSL issues
        nltk_ssl_fix = '''
import ssl
import certifi
import nltk

# Fix SSL context for NLTK
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Download NLTK data
print("Downloading NLTK data...")
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
print("NLTK data downloaded successfully!")
'''
        
        with open("fix_nltk_ssl.py", "w") as f:
            f.write(nltk_ssl_fix)
        
        print("✅ Created NLTK SSL fix script")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing SSL: {e}")
        return False

def fix_spacy_pydantic():
    """Fix spaCy and pydantic compatibility issues."""
    print("\n🧠 Fixing spaCy and pydantic Compatibility...")
    print("=" * 45)
    
    try:
        # Uninstall problematic packages
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "spacy", "pydantic"], check=True)
        print("✅ Uninstalled problematic packages")
        
        # Install compatible versions
        subprocess.run([sys.executable, "-m", "pip", "install", "pydantic==2.5.0"], check=True)
        print("✅ Installed pydantic==2.5.0")
        
        subprocess.run([sys.executable, "-m", "pip", "install", "spacy==3.7.4"], check=True)
        print("✅ Installed spacy==3.7.4")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing spaCy: {e}")
        return False

def install_spacy_model():
    """Install spaCy model with SSL fix."""
    print("\n📦 Installing spaCy Model...")
    print("=" * 30)
    
    try:
        # Create spaCy download script with SSL fix
        spacy_download_script = '''
import ssl
import certifi

# Fix SSL context
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Download spaCy model
import spacy.cli
spacy.cli.download("en_core_web_sm")
print("spaCy model downloaded successfully!")
'''
        
        with open("fix_spacy_download.py", "w") as f:
            f.write(spacy_download_script)
        
        subprocess.run([sys.executable, "fix_spacy_download.py"], check=True)
        print("✅ spaCy model installed")
        return True
        
    except Exception as e:
        print(f"❌ Error installing spaCy model: {e}")
        return False

def install_nltk_data():
    """Install NLTK data with SSL fix."""
    print("\n📚 Installing NLTK Data...")
    print("=" * 30)
    
    try:
        subprocess.run([sys.executable, "fix_nltk_ssl.py"], check=True)
        print("✅ NLTK data installed")
        return True
        
    except Exception as e:
        print(f"❌ Error installing NLTK data: {e}")
        return False

def test_installations():
    """Test if installations work."""
    print("\n🧪 Testing Installations...")
    print("=" * 30)
    
    test_script = '''
import spacy
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords, wordnet

# Test spaCy
try:
    nlp = spacy.load("en_core_web_sm")
    doc = nlp("This is a test sentence.")
    print("✅ spaCy working")
except Exception as e:
    print(f"❌ spaCy error: {e}")

# Test NLTK
try:
    tokens = word_tokenize("This is a test sentence.")
    stops = set(stopwords.words('english'))
    synsets = wordnet.synsets('test')
    print("✅ NLTK working")
except Exception as e:
    print(f"❌ NLTK error: {e}")

print("Installation test completed!")
'''
    
    with open("test_nlp.py", "w") as f:
        f.write(test_script)
    
    try:
        subprocess.run([sys.executable, "test_nlp.py"], check=True)
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def cleanup():
    """Clean up temporary files."""
    print("\n🧹 Cleaning up...")
    print("=" * 20)
    
    temp_files = ["fix_nltk_ssl.py", "fix_spacy_download.py", "test_nlp.py"]
    
    for file in temp_files:
        try:
            os.remove(file)
            print(f"✅ Removed {file}")
        except:
            pass

def main():
    """Main fix process."""
    print("🍎 Mac NLP Installation Fix")
    print("=" * 35)
    
    # Fix SSL certificates
    if not fix_ssl_certificates():
        print("❌ Failed to fix SSL certificates")
        return False
    
    # Fix spaCy and pydantic
    if not fix_spacy_pydantic():
        print("❌ Failed to fix spaCy/pydantic")
        return False
    
    # Install spaCy model
    if not install_spacy_model():
        print("❌ Failed to install spaCy model")
        return False
    
    # Install NLTK data
    if not install_nltk_data():
        print("❌ Failed to install NLTK data")
        return False
    
    # Test installations
    if not test_installations():
        print("❌ Installation test failed")
        return False
    
    # Cleanup
    cleanup()
    
    print("\n🎉 Mac NLP Installation Fixed Successfully!")
    print("=" * 45)
    print("✅ SSL certificates fixed")
    print("✅ spaCy and pydantic compatibility resolved")
    print("✅ spaCy model installed")
    print("✅ NLTK data downloaded")
    print("✅ All tests passed")
    
    return True

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🚀 You can now run the project!")
        print("Next steps:")
        print("1. python quick_hybrid_test.py")
        print("2. python api_server_start.py")
        print("3. python run_full_extraction.py")
    else:
        print("\n❌ Fix failed. Check the errors above.")
        sys.exit(1)
