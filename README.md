# Philanthropic Ideas Generator

A comprehensive system for identifying and evaluating high-impact philanthropic opportunities across multiple domains including human health, animal welfare, economic development, climate change, and overall wellbeing.

## Project Overview

This system analyzes data from multiple sources to identify:
1. **Newly viable ideas** - Opportunities enabled by recent technological, scientific, cultural, or political shifts
2. **Evergreen ideas** - Obvious but neglected opportunities that remain undone

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

## Getting Started

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment:**
   - Copy `env_template.txt` to `.env`
   - Add your API keys to the `.env` file
   - For talent identification, set up Google Custom Search API (see `GOOGLE_SEARCH_SETUP.md`)

3. **Initialize and start the system:**
   ```bash
   python run.py
   ```
   This will:
   - Check dependencies
   - Set up the environment file
   - Download required NLP models
   - Initialize the database
   - Provide a menu to start the API server or run tests

4. **Start the API server:**
   - Choose option 1 from the menu, or run directly:
   ```bash
   python -m api.main
   ```

5. **Access the web interface:**
   - Open `http://localhost:8000/web_interface/index.html` in your browser
   - Or visit `http://localhost:8000/docs` for API documentation

6. **Test caching functionality:**
   - Choose option 4 from the menu, or run directly:
   ```bash
   python test_cache.py
   ```

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
