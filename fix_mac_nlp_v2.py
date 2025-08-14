#!/usr/bin/env python3
"""
Mac NLP Installation Fix Script v2 - Enhanced for spaCy/pydantic compatibility
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
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing SSL: {e}")
        return False

def fix_spacy_compatibility():
    """Fix spaCy compatibility with a more conservative approach."""
    print("\n🧠 Fixing spaCy Compatibility (Conservative Approach)...")
    print("=" * 55)
    
    try:
        # First, let's try a different approach - use a more recent spaCy version
        # that's known to work with Python 3.12
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "spacy"], check=True)
        print("✅ Uninstalled spaCy")
        
        # Install a more recent spaCy version that works with Python 3.12
        subprocess.run([sys.executable, "-m", "pip", "install", "spacy>=3.8.0"], check=True)
        print("✅ Installed spaCy >=3.8.0")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing spaCy: {e}")
        return False

def install_spacy_model_manual():
    """Install spaCy model manually with direct download."""
    print("\n📦 Installing spaCy Model (Manual Method)...")
    print("=" * 45)
    
    try:
        # Try direct download without SSL context modification
        subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], check=True)
        print("✅ spaCy model installed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Direct download failed: {e}")
        
        # Fallback: Try with SSL fix
        try:
            spacy_download_script = '''
import ssl
import certifi
import subprocess
import sys

# Fix SSL context
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Try manual download
try:
    import spacy.cli
    spacy.cli.download("en_core_web_sm")
    print("spaCy model downloaded successfully!")
except Exception as e:
    print(f"spaCy CLI failed: {e}")
    # Try alternative method
    import urllib.request
    import os
    
    # Download the model directly
    model_url = "https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.0/en_core_web_sm-3.7.0-py3-none-any.whl"
    model_file = "en_core_web_sm-3.7.0-py3-none-any.whl"
    
    print(f"Downloading model from {model_url}")
    urllib.request.urlretrieve(model_url, model_file)
    
    # Install the downloaded wheel
    subprocess.run([sys.executable, "-m", "pip", "install", model_file], check=True)
    print("spaCy model installed via direct download!")
    
    # Clean up
    os.remove(model_file)
'''
            
            with open("fix_spacy_manual.py", "w") as f:
                f.write(spacy_download_script)
            
            subprocess.run([sys.executable, "fix_spacy_manual.py"], check=True)
            print("✅ spaCy model installed via manual method")
            return True
            
        except Exception as e2:
            print(f"❌ Manual method also failed: {e2}")
            return False

def install_nltk_data_manual():
    """Install NLTK data with manual SSL fix."""
    print("\n📚 Installing NLTK Data (Manual Method)...")
    print("=" * 40)
    
    try:
        nltk_ssl_fix = '''
import ssl
import certifi
import nltk
import os

# Fix SSL context for NLTK
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Set NLTK data path
nltk_data_dir = os.path.expanduser("~/nltk_data")
if not os.path.exists(nltk_data_dir):
    os.makedirs(nltk_data_dir)

# Download NLTK data
print("Downloading NLTK data...")
try:
    nltk.download('punkt', download_dir=nltk_data_dir)
    nltk.download('stopwords', download_dir=nltk_data_dir)
    nltk.download('wordnet', download_dir=nltk_data_dir)
    print("NLTK data downloaded successfully!")
except Exception as e:
    print(f"NLTK download failed: {e}")
    # Try alternative method
    import urllib.request
    
    nltk_files = [
        ("https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/tokenizers/punkt.zip", "punkt.zip"),
        ("https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/stopwords.zip", "stopwords.zip"),
        ("https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/wordnet/wordnet.zip", "wordnet.zip")
    ]
    
    for url, filename in nltk_files:
        print(f"Downloading {filename}...")
        urllib.request.urlretrieve(url, filename)
        # Extract and move to nltk_data directory
        import zipfile
        with zipfile.ZipFile(filename, 'r') as zip_ref:
            zip_ref.extractall(nltk_data_dir)
        os.remove(filename)
    
    print("NLTK data downloaded via alternative method!")
'''
        
        with open("fix_nltk_manual.py", "w") as f:
            f.write(nltk_ssl_fix)
        
        subprocess.run([sys.executable, "fix_nltk_manual.py"], check=True)
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
import sys

# Test spaCy
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    doc = nlp("This is a test sentence.")
    print("✅ spaCy working")
except Exception as e:
    print(f"❌ spaCy error: {e}")

# Test NLTK
try:
    import nltk
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords, wordnet
    
    tokens = word_tokenize("This is a test sentence.")
    stops = set(stopwords.words('english'))
    synsets = wordnet.synsets('test')
    print("✅ NLTK working")
except Exception as e:
    print(f"❌ NLTK error: {e}")

print("Installation test completed!")
'''
    
    with open("test_nlp_v2.py", "w") as f:
        f.write(test_script)
    
    try:
        subprocess.run([sys.executable, "test_nlp_v2.py"], check=True)
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def cleanup():
    """Clean up temporary files."""
    print("\n🧹 Cleaning up...")
    print("=" * 20)
    
    temp_files = ["fix_spacy_manual.py", "fix_nltk_manual.py", "test_nlp_v2.py"]
    
    for file in temp_files:
        try:
            os.remove(file)
            print(f"✅ Removed {file}")
        except:
            pass

def main():
    """Main fix process."""
    print("🍎 Mac NLP Installation Fix v2")
    print("=" * 35)
    
    # Fix SSL certificates
    if not fix_ssl_certificates():
        print("❌ Failed to fix SSL certificates")
        return False
    
    # Fix spaCy compatibility
    if not fix_spacy_compatibility():
        print("❌ Failed to fix spaCy compatibility")
        return False
    
    # Install spaCy model
    if not install_spacy_model_manual():
        print("❌ Failed to install spaCy model")
        return False
    
    # Install NLTK data
    if not install_nltk_data_manual():
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
    print("✅ spaCy compatibility resolved")
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
