# Mac Python 3.12 Installation Guide

## Overview
This guide provides step-by-step instructions for installing the philanthropic ideas project on macOS with Python 3.12.

## Prerequisites

### 1. System Requirements
- macOS 10.15 (Catalina) or later
- At least 4GB RAM
- 2GB free disk space

### 2. Required Tools

#### Install Xcode Command Line Tools
```bash
xcode-select --install
```
This may take 10-15 minutes. Follow the prompts in the popup window.

#### Install Homebrew (Package Manager)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

After installation, add Homebrew to your PATH:
```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

#### Install Python 3.12
```bash
brew install python@3.12
```

Verify installation:
```bash
python3.12 --version
```

## Installation Steps

### 1. Clone the Repository
```bash
git clone <repository-url>
cd philanthropic-ideas
```

### 2. Create Virtual Environment
```bash
python3.12 -m venv venv
source venv/bin/activate
```

### 3. Upgrade Build Tools
```bash
pip install --upgrade pip setuptools wheel
```

### 4. Install Requirements
```bash
pip install -r requirements-mac-py312.txt
```

### 5. Install spaCy Model
```bash
python -m spacy download en_core_web_sm
```

### 6. Install NLTK Data
```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
```

## Common Issues & Solutions

### 1. psycopg2-binary Installation Issues
**Problem**: `psycopg2-binary` fails to install
**Solution**:
```bash
brew install postgresql
pip install psycopg2-binary==2.9.9
```

### 2. matplotlib Backend Issues
**Problem**: matplotlib doesn't display plots
**Solution**:
```bash
mkdir -p ~/.matplotlib
echo "backend: TkAgg" > ~/.matplotlib/matplotlibrc
```

### 3. SSL Certificate Issues
**Problem**: SSL certificate errors during package installation
**Solution**:
```bash
pip install certifi --upgrade
```

### 4. Permission Issues
**Problem**: Permission denied errors
**Solution**:
```bash
pip install --user package_name
```

### 5. Architecture Issues (M1/M2 Macs)
**Problem**: Package compatibility with Apple Silicon
**Solution**:
```bash
# For ARM64 (native)
arch -arm64 pip install package_name

# For x86_64 (Rosetta)
arch -x86_64 pip install package_name
```

### 6. Memory Issues
**Problem**: Out of memory during installation
**Solution**:
```bash
# Increase swap space or close other applications
# Install packages one by one if needed
pip install fastapi
pip install uvicorn
# ... continue with other packages
```

## Post-Installation Setup

### 1. Environment Configuration
```bash
cp env_template.txt .env
# Edit .env with your API keys
```

### 2. Database Initialization
```bash
python -c "from storage.database import db_manager; db_manager.create_tables()"
```

### 3. Test Installation
```bash
python quick_hybrid_test.py
```

### 4. Start the Application
```bash
# Start API server
python api_server_start.py

# Open frontend (in another terminal)
open web_interface/index.html
```

## Troubleshooting

### Package-Specific Issues

#### spaCy Issues
```bash
# Reinstall spaCy
pip uninstall spacy
pip install spacy>=3.7.4
python -m spacy download en_core_web_sm
```

#### NLTK Issues
```bash
# Download NLTK data manually
python -c "import nltk; nltk.download('all')"
```

#### Transformers/Torch Issues
```bash
# Install PyTorch for Mac
pip install torch torchvision torchaudio
```

### System-Specific Issues

#### M1/M2 Mac Issues
- Use `arch -arm64` for native ARM64 packages
- Use `arch -x86_64` for x86_64 packages via Rosetta
- Some packages may not have ARM64 wheels yet

#### Intel Mac Issues
- Most packages should work normally
- Use standard installation commands

### Performance Optimization

#### For M1/M2 Macs
```bash
# Use native ARM64 Python
arch -arm64 python3.12

# Optimize for performance
export PYTHONOPTIMIZE=1
```

#### For Intel Macs
```bash
# Standard optimization
export PYTHONOPTIMIZE=1
```

## Verification

### Test All Components
```bash
# Test core packages
python -c "import fastapi, uvicorn, sqlalchemy, pandas, numpy, spacy, nltk, openai; print('All packages imported successfully!')"

# Test database connection
python -c "from storage.database import db_manager; print('Database connection successful!')"

# Test API server
python api_server_start.py &
sleep 5
curl http://localhost:8000/health
kill %1
```

## Next Steps

1. **Configure API Keys**: Add your OpenAI API key to `.env`
2. **Run Data Ingestion**: Execute the data ingestion pipeline
3. **Generate Ideas**: Run the hybrid idea extraction
4. **Evaluate Ideas**: Score and rank the generated ideas
5. **Explore Frontend**: Use the web interface to browse results

## Support

If you encounter issues:
1. Check this guide for common solutions
2. Verify your Python version: `python3.12 --version`
3. Check package versions: `pip list`
4. Review error logs for specific issues
5. Ensure all prerequisites are installed

## Additional Resources

- [Python 3.12 Documentation](https://docs.python.org/3.12/)
- [Homebrew Documentation](https://docs.brew.sh/)
- [spaCy Documentation](https://spacy.io/usage)
- [NLTK Documentation](https://www.nltk.org/)
