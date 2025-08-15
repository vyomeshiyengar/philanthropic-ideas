# Philanthropic Ideas Generator

A comprehensive system for identifying and evaluating high-impact philanthropic opportunities across multiple domains including human health, animal welfare, economic development, climate change, and overall wellbeing.

## Project Overview

This system analyzes data from multiple sources to identify:
1. **Newly viable ideas** - Opportunities enabled by recent technological, scientific, cultural, or political shifts
2. **Evergreen ideas** - Obvious but neglected opportunities that remain undone

## 📋 Installation

**For detailed installation instructions for Windows, Mac, and Linux, see [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)**

### Quick Start:
- **Windows**: `pip install -r requirements-windows.txt`
- **Mac Python 3.12**: `pip install -r requirements-mac-py312.txt`
- **Linux/Other**: `pip install -r requirements.txt`

## Target Outcomes & Metrics

The system evaluates ideas across these key metrics:
- **DALYs** (Disability-Adjusted Life Years) - Health interventions
- **WALYs** (Welfare-Adjusted Life Years) - Animal welfare
- **Log Income** - Economic development, especially in LMICs
- **CO₂-equivalent reduction** - Climate impact
- **WELBYs** (Wellbeing-Adjusted Life Years) - Overall wellbeing
- **Proxy metrics** - Correlated outcomes (GDP, education, etc.)

## Data Sources

### Research & Evidence
- **OpenAlex** - Academic papers and research
- **PubMed** - Medical and scientific literature
- **Semantic Scholar** - Academic paper search
- **World Bank** - Development indicators
- **IHME GBD** - Global burden of disease data

### Funding & Neglectedness
- **NIH RePORTER** - NIH-funded projects
- **CORDIS** - EU research projects
- **World Bank Projects** - Development projects

### Expert Analysis
- Various Substack channels and blogs from thought leaders in effective altruism, development economics, and policy

## Project Structure

```
philanthropic-ideas/
├── data_ingestion/          # Data collection from various APIs
├── analysis/                # Data processing and opportunity identification
├── scoring/                 # Idea evaluation and ranking
├── storage/                 # Database and data management
├── api/                     # REST API for the system
├── web_interface/           # Frontend for idea exploration
├── config/                  # Configuration files
├── tests/                   # Test suite
└── docs/                    # Documentation
```

## Key Features

1. **Multi-source data ingestion** with rate limiting and error handling
2. **Opportunity identification** using NLP and pattern recognition
3. **Comparative analysis** against benchmark interventions
4. **Neglectedness scoring** based on funding data
5. **Talent identification** using Crunchbase and web search
6. **Contrarian ranking** to challenge conventional wisdom

## Complete Setup Guide

This guide will walk you through setting up the Philanthropic Ideas Generator from scratch.

### Prerequisites

Before you begin, make sure you have:

1. **Python 3.12** installed on your system
   - Download from [python.org](https://www.python.org/downloads/)
   - Make sure to check "Add Python to PATH" during installation
   - Verify installation: `python --version` should show Python 3.12.x

2. **Git** installed (for cloning the repository)
   - Download from [git-scm.com](https://git-scm.com/)
   - Verify installation: `git --version`

3. **A code editor** (VS Code, PyCharm, etc.)

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/philanthropic-ideas.git
cd philanthropic-ideas
```

### Step 2: Set Up Python Environment

**Windows (PowerShell):**
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Upgrade pip, setuptools, and wheel
python -m pip install --upgrade pip setuptools wheel
```

**macOS/Linux:**
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip, setuptools, and wheel
python -m pip install --upgrade pip setuptools wheel
```

### Step 3: Install Dependencies

**For Python 3.12+ (Recommended):**
```bash
# Use the Python 3.12 compatible requirements file
pip install -r requirements-py312.txt
```

**For older Python versions:**
```bash
# Use the original requirements file
pip install -r requirements.txt
```

**Note:** If you encounter issues with `wordcloud` on Python 3.12+, the package has been removed from the Python 3.12 requirements file as it's not essential for core functionality.

**Alternative: Use the installation script**
```bash
# Run the automated installation script
python install.py
```

This script will:
- Detect your Python version
- Install appropriate dependencies
- Download required spaCy and NLTK models
- Provide troubleshooting tips if needed

**macOS/Linux:**
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip, setuptools, and wheel
python -m pip install --upgrade pip setuptools wheel
```

### Step 3: Install Dependencies

```bash
# Install PyTorch (CPU version for Python 3.12)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install all other dependencies
pip install -r requirements.txt
```

**Note:** If you encounter any installation errors:
- Make sure you're using Python 3.12
- Try installing packages one by one to identify problematic ones
- On Windows, you might need to install Visual Studio Build Tools for some packages

### Step 4: Set Up Environment Variables

1. **Copy the environment template:**
   ```bash
   cp env_template.txt .env
   ```

2. **Edit the `.env` file** and add your API keys:
   ```env
   # Database Configuration
   DATABASE_URL=sqlite:///./philanthropic_ideas.db
   REDIS_URL=redis://localhost:6379

   # API Keys (get these from respective services)
   # OpenAlex free API doesn't require authentication
   OPENALEX_API_KEY=
   SEMANTIC_SCHOLAR_API_KEY=your_semantic_scholar_api_key_here
   CRUNCHBASE_API_KEY=your_crunchbase_api_key_here
   
   # Google Custom Search API (for talent identification)
   # Get from: https://developers.google.com/custom-search/v1/overview
   GOOGLE_API_KEY=AIzaSyCPm3TFfqrG8nAFYtDgBAE6JiKYZV26iPk
   GOOGLE_CUSTOM_SEARCH_ENGINE_ID=a6faf4d3140ef4b28
   
   # NIH RePORTER API (for research funding data)
   NIH_API_KEY=da1855ba8b0acd7360ff329610ca03cd1b08

   # Rate Limiting (requests per hour)
   OPENALEX_RATE_LIMIT=100
   SEMANTIC_SCHOLAR_RATE_LIMIT=100
   CRUNCHBASE_RATE_LIMIT=1000
   GOOGLE_RATE_LIMIT=100

   # Logging
   LOG_LEVEL=INFO

   # Development Settings
   DEBUG=True
   ```

   **⚠️ IMPORTANT:** The API keys shown above are for development purposes. For production use, you should:
   - Generate your own API keys from the respective services
   - Never commit the `.env` file to version control (it's already in `.gitignore`)
   - Use environment-specific keys for different deployments

### Step 5: Initialize the System

Run the setup script:
```bash
python run.py
```

This will:
- Check if all dependencies are installed
- Download required NLP models (NLTK data, spaCy models)
- Initialize the database
- Set up the environment file if it doesn't exist

### Step 6: Test the Installation

1. **Run the prototype test:**
   ```bash
   python test_prototype.py
   ```
   This should show "All tests passed!" if everything is set up correctly.

2. **Test the API server:**
   ```bash
   python -m api.main
   ```
   Then open `http://localhost:8000` in your browser.

### Step 7: Optional - Set Up Google Custom Search API

For talent identification functionality:

1. **Follow the detailed guide:** See `GOOGLE_SEARCH_SETUP.md`
2. **Or use the quick setup:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Enable Custom Search API
   - Create API credentials
   - Go to [Google Custom Search Engine](https://cse.google.com/)
   - Create a search engine configured to search the entire web
   - Add the API key and Search Engine ID to your `.env` file

### Step 8: Start Using the System

1. **Start the API server:**
   ```bash
   python run.py
   # Choose option 1: Start API server
   ```

2. **Access the web interface:**
   - Open `http://localhost:8000/web` in your browser
   - Or visit `http://localhost:8000/docs` for API documentation

3. **Run the prototype pipeline:**
   - Click "Run Prototype Pipeline" in the web interface
   - This will ingest data from OpenAlex, NIH RePORTER, and web scraping
   - View the results in the web interface

### Troubleshooting Common Issues

**"No module named 'sqlalchemy'" or similar errors:**
- Make sure you're in the virtual environment (you should see `(.venv)` in your terminal)
- Reinstall dependencies: `pip install -r requirements.txt`

**"Python command not found":**
- Make sure Python 3.12 is installed and added to PATH
- On Windows, try using `py` instead of `python`

**"Permission denied" errors on Windows:**
- Run PowerShell as Administrator
- Or change execution policy: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

**"Failed to install torch":**
- Try the CPU-only version: `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu`
- Or install from conda if you have Anaconda installed

**"Database connection failed":**
- Make sure you have write permissions in the project directory
- The SQLite database will be created automatically

**"API endpoints returning 500 errors":**
- Check that all dependencies are installed correctly
- Run `python test_prototype.py` to identify specific issues
- Check the logs for detailed error messages

### Getting API Keys

**OpenAlex:** No API key required (free service)

**NIH RePORTER:** 
- Go to [NIH RePORTER](https://reporter.nih.gov/)
- Register for an account
- Get your API key from the developer section

**Google Custom Search API:**
- See `GOOGLE_SEARCH_SETUP.md` for detailed instructions
- Requires Google Cloud Platform account with billing enabled

**Other APIs (optional):**
- Semantic Scholar: [semanticscholar.org](https://www.semanticscholar.org/product/api)
- Crunchbase: [crunchbase.com/api](https://www.crunchbase.com/api)

### Next Steps

Once the system is running:

1. **Explore the web interface** to understand the features
2. **Run the prototype pipeline** to see data ingestion in action
3. **Check the API documentation** at `http://localhost:8000/docs`
4. **Read the code** to understand how it works
5. **Customize the configuration** in `config/settings.py`

### Support

If you encounter issues:
1. Check the troubleshooting section above
2. Run `python test_prototype.py` to identify problems
3. Check the logs for error messages
4. Create an issue in the GitHub repository with details about your setup

## Caching System

The system includes a comprehensive caching mechanism for API responses that provides:

### Benefits
- **Performance**: Cached responses are served instantly instead of making new API calls
- **Rate Limit Protection**: Reduces API calls to stay within rate limits
- **Cost Savings**: Fewer API calls mean lower costs for paid APIs
- **Offline Access**: Once cached, data can be accessed without internet
- **Reliability**: Reduces dependency on external API availability

### How It Works
1. **Cache Key Generation**: Each API request generates a unique cache key based on:
   - Source name (e.g., "openalex", "pubmed")
   - Query string
   - Request parameters

2. **Cache Storage**: Responses are stored in the `.cache` directory as pickle files with:
   - Response data
   - Timestamp
   - Time-to-live (TTL) settings

3. **Cache Lookup**: Before making an API call, the system checks for cached responses

4. **Automatic Expiration**: Cache entries expire after 1 hour by default (configurable)

### Cache Management
- **View Statistics**: Use the "Cache Stats" button in the web interface or call `/cache/stats`
- **Clear Cache**: Use the "Clear Cache" button or call `/cache/clear`
- **Invalidate Specific Entries**: Call `/cache/invalidate?source=openalex&query=education`

### Example Cache Performance
```
First API call: 2.5 seconds
Cached response: 0.02 seconds
Speedup: 125x faster!
```

### Configuration
Cache settings can be modified in `storage/cache.py`:
- `default_ttl`: Time-to-live for cache entries (default: 3600 seconds)
- `cache_dir`: Directory for cache files (default: ".cache")

## Benchmarks

- **Health/DALYs**: GiveWell interventions
- **Animal Welfare/WALYs**: The Humane League
- **Wellbeing/WELBYs**: StrongMinds
- **Economic Development**: GiveDirectly
- **Climate**: Cheapest scalable carbon removal

## License

MIT License
