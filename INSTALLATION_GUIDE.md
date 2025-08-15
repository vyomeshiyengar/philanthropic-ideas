# Installation Guide - Philanthropic Ideas Generator

This guide covers installation for Windows, Mac, and Linux systems.

## Prerequisites

- Python 3.12+ (recommended) or Python 3.11+
- pip (Python package installer)
- Git

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/vyomeshiyengar/philanthropic-ideas.git
cd philanthropic-ideas
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

#### For Windows:
```bash
pip install -r requirements-windows.txt
```

#### For Mac Python 3.12:
```bash
pip install -r requirements-mac-py312.txt
```

#### For Linux/Other:
```bash
pip install -r requirements.txt
```

### 4. Install NLP Models
```bash
# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('averaged_perceptron_tagger'); nltk.download('maxent_ne_chunker'); nltk.download('words')"

# For spaCy (optional - system works without it)
python -m spacy download en_core_web_sm
```

### 5. Set Up Environment
```bash
# Copy environment template
cp env_template.txt .env

# Edit .env file with your API keys
# Add your OpenAI API key: OPENAI_API_KEY=your_key_here
```

### 6. Initialize Database
```bash
python -c "from storage.database import db_manager; db_manager.create_tables()"
```

## Platform-Specific Instructions

### Windows

#### Prerequisites:
- Python 3.12+ from python.org
- Visual Studio Build Tools (for some packages)

#### Installation:
```bash
# Use Windows requirements
pip install -r requirements-windows.txt

# If you encounter build errors, install Visual Studio Build Tools
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

### Mac

#### Prerequisites:
- Xcode Command Line Tools
- Homebrew (recommended)

#### Installation:
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Use Mac requirements
pip install -r requirements-mac-py312.txt
```

#### Troubleshooting Mac Issues:
If you encounter spaCy/pydantic compatibility issues:
```bash
# The system works without spaCy - NLTK fallback is available
# If you want to use spaCy, try:
pip uninstall spacy pydantic
pip install pydantic==2.5.0
pip install spacy>=3.8.0
python -m spacy download en_core_web_sm
```

### Linux (Ubuntu/Debian)

#### Prerequisites:
```bash
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev
sudo apt install build-essential libssl-dev libffi-dev
```

#### Installation:
```bash
pip install -r requirements.txt
```

## Running the Application

### 1. Start the API Server
```bash
python start_server.py
```

### 2. Access the Frontend
Open your browser and go to: `http://localhost:8000/web_interface/index.html`

### 3. Alternative Server Start
```bash
# Using uvicorn directly
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Using Python module
python -m api.main
```

## Testing the Installation

### 1. Test Basic Functionality
```bash
python test_nltk_fallback.py
```

### 2. Test API Server
```bash
python test_frontend.py
```

### 3. Test Full Extraction
```bash
python run_full_extraction_with_progress.py
```

## Troubleshooting

### Common Issues

#### 1. ModuleNotFoundError: No module named 'ratelimit'
```bash
pip install ratelimit==2.2.1
```

#### 2. spaCy Import Errors (Mac)
The system works without spaCy. If you want to use it:
```bash
pip uninstall spacy pydantic
pip install pydantic==2.5.0
pip install spacy>=3.8.0
```

#### 3. Build Errors (Windows)
Install Visual Studio Build Tools:
- Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
- Install with C++ build tools

#### 4. SSL Certificate Errors (Mac)
```bash
# Install certificates
pip install certifi
python -c "import ssl; print(ssl.get_default_verify_paths())"
```

#### 5. Port Already in Use
```bash
# Kill existing processes
taskkill /f /im python.exe  # Windows
pkill -f python  # Mac/Linux

# Or use a different port
uvicorn api.main:app --port 8001
```

### Dependencies Overview

#### Core Dependencies:
- **FastAPI**: Web framework
- **SQLAlchemy**: Database ORM
- **NLTK**: Natural language processing
- **OpenAI**: AI integration
- **aiohttp**: Async HTTP client
- **BeautifulSoup**: Web scraping

#### Platform-Specific:
- **Windows**: Additional build tools and SSL certificates
- **Mac**: Xcode tools and Homebrew
- **Linux**: System development packages

## File Structure

```
philanthropic-ideas/
├── requirements.txt              # General requirements
├── requirements-windows.txt      # Windows-specific
├── requirements-mac-py312.txt    # Mac Python 3.12
├── requirements-py312.txt        # Python 3.12 general
├── api/                         # API server
├── analysis/                    # Idea extraction
├── data_ingestion/             # Data collection
├── scoring/                    # Idea evaluation
├── storage/                    # Database models
├── web_interface/              # Frontend
└── config/                     # Configuration
```

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Ensure you're using the correct requirements file for your platform
3. Verify Python version compatibility
4. Check that all dependencies are installed correctly

The system is designed to work without spaCy (using NLTK fallback), so most issues can be resolved by using the appropriate requirements file for your platform.

