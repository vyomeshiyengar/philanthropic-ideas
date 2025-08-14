# Mac Quick Start Guide

## 🚀 Quick Installation for Mac Python 3.12

### Prerequisites (5 minutes)
```bash
# 1. Install Xcode Command Line Tools
xcode-select --install

# 2. Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 3. Install Python 3.12
brew install python@3.12
```

### Installation (10 minutes)
```bash
# 1. Clone and setup
git clone <repository-url>
cd philanthropic-ideas

# 2. Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# 3. Install requirements
pip install -r requirements-mac-py312.txt

# 4. Install NLP models
python -m spacy download en_core_web_sm
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
```

### Quick Test (2 minutes)
```bash
# Test installation
python quick_hybrid_test.py

# Start the application
python api_server_start.py
```

## 🔧 Common Mac Issues

### M1/M2 Mac Issues
```bash
# Use native ARM64
arch -arm64 pip install package_name

# Or use Rosetta for x86_64
arch -x86_64 pip install package_name
```

### psycopg2-binary Issues
```bash
brew install postgresql
pip install psycopg2-binary==2.9.9
```

### matplotlib Issues
```bash
mkdir -p ~/.matplotlib
echo "backend: TkAgg" > ~/.matplotlib/matplotlibrc
```

## 📋 What's Different for Mac

✅ **Removed**: `wordcloud` (configparser issues)  
✅ **Added**: Mac-specific SSL packages  
✅ **Updated**: Package versions for Python 3.12  
✅ **Added**: Architecture-specific instructions  

## 🎯 Next Steps

1. Add your OpenAI API key to `.env`
2. Run `python run_full_extraction.py` to generate ideas
3. Open `web_interface/index.html` to view results

## 📖 Full Guide

For detailed troubleshooting, see `MAC_INSTALLATION_GUIDE.md`
