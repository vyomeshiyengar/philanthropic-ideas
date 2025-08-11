# Philanthropic Ideas Generator - Prototype

This prototype focuses on three data sources: **OpenAlex**, **NIH RePORTER**, and **Web Scraper** (for expert blogs and Substack channels).

## 🚀 Quick Start

### 1. Setup
```bash
# Activate your virtual environment
.\.venv\Scripts\Activate.ps1  # Windows PowerShell
source .venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env_template.txt .env
# Edit .env with your API keys (OpenAlex, NIH RePORTER, Google Search)
```

### 2. Test the Prototype
```bash
python run.py
# Choose option 5: "Run prototype test"
```

### 3. Start the Web Interface
```bash
python run.py
# Choose option 1: "Start API server"
```

Then open: http://localhost:8000

## 🎯 Prototype Features

### Data Sources (Enabled)
- **OpenAlex**: Academic papers and research
- **NIH RePORTER**: Funded research projects
- **Web Scraper**: Expert blogs and Substack channels

### Data Sources (Disabled for Prototype)
- PubMed
- Semantic Scholar
- World Bank
- CORDIS

### Core Functionality
1. **Data Ingestion**: Collects data from the three enabled sources
2. **Idea Extraction**: Uses NLP to identify philanthropic opportunities
3. **Idea Evaluation**: Scores ideas on impact, neglectedness, tractability, scalability
4. **Talent Identification**: Finds potential people to work on top ideas (Google Search only)

## 📊 Web Interface

The web interface provides:

### Prototype Pipeline Section
- **Run Prototype Pipeline**: Executes the full workflow
- **Check Status**: Shows current data and idea counts
- **View Results**: Displays raw data and extracted ideas

### Results Display
- **Raw Data**: Shows ingested content from each source
- **Extracted Ideas**: Displays ideas with thought process explanations
- **Top Ideas**: Shows highest-scoring opportunities

### Thought Process
Each extracted idea includes reasoning for:
- Domain classification
- Idea type (newly viable vs evergreen)
- Confidence scoring
- Primary metric assignment

## 🔧 Configuration

### API Keys Required
- `OPENALEX_API_KEY`: For academic paper search
- `NIH_API_KEY`: For research project data
- `GOOGLE_API_KEY`: For talent identification

### Settings
- Only OpenAlex, NIH RePORTER, and Web Scraper are enabled
- Other sources are disabled but remain configured
- Talent identification uses Google Search API only (no Crunchbase)

## 📈 Expected Output

### Data Ingestion
- OpenAlex: Academic papers on philanthropic topics
- NIH RePORTER: Funded research projects
- Web Scraper: Expert blog posts and articles

### Idea Extraction
- Domain classification (health, education, economic_development, etc.)
- Primary metric assignment (DALYs, WALYs, log_income, CO2, WELBYs)
- Idea type classification (newly viable vs evergreen)
- Confidence scoring with reasoning

### Evaluation
- Impact scores based on potential outcomes
- Neglectedness scores based on funding levels
- Tractability scores based on implementation feasibility
- Scalability scores based on potential reach

### Talent Identification
- Google Search-based candidate identification
- Fit scoring based on expertise and experience
- Match reasoning for each candidate

## 🧪 Testing

Run the comprehensive test suite:
```bash
python test_prototype.py
```

This tests:
- Database connectivity
- Configuration loading
- Component initialization
- API endpoints (if server is running)

## 🔄 Workflow

1. **Start the server**: `python run.py` → Option 1
2. **Open web interface**: http://localhost:8000
3. **Run prototype pipeline**: Click "Run Prototype Pipeline"
4. **Monitor progress**: Check status updates
5. **View results**: Click "View Results" to see data and ideas
6. **Explore ideas**: Review extracted ideas with thought processes

## 🐛 Troubleshooting

### Common Issues
1. **Missing API keys**: Set up your `.env` file with required keys
2. **Database errors**: Run `python test_prototype.py` to check setup
3. **Import errors**: Ensure virtual environment is activated
4. **Server not starting**: Check if port 8000 is available

### Logs
- Check console output for detailed logging
- API server logs show ingestion progress
- Database operations are logged with timestamps

## 📝 Next Steps

After testing the prototype:
1. Review extracted ideas and their reasoning
2. Check the quality of data ingestion
3. Evaluate the thought process explanations
4. Consider enabling additional data sources
5. Refine the idea extraction algorithms

## 🔗 API Endpoints

### Prototype-Specific
- `POST /prototype/run`: Start prototype pipeline
- `GET /prototype/status`: Get current status
- `GET /prototype/raw-data`: Get ingested data
- `GET /prototype/ideas`: Get extracted ideas

### General
- `GET /health`: API health check
- `GET /cache/stats`: Cache statistics
- `DELETE /cache/clear`: Clear cache

## 📊 Metrics

The prototype evaluates ideas using:
- **DALYs**: Disability-Adjusted Life Years (health)
- **WALYs**: Welfare-Adjusted Life Years (animals)
- **WELBYs**: Wellbeing-Adjusted Life Years (general)
- **Log Income**: Economic development
- **CO2**: Climate impact

Each idea is scored on:
- **Impact**: Potential positive outcomes
- **Neglectedness**: Current funding levels
- **Tractability**: Implementation feasibility
- **Scalability**: Potential reach and adoption
