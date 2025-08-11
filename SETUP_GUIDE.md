# Philanthropic Ideas Generator - Setup Guide

## Prerequisites
- Python 3.12 installed
- Git installed
- PowerShell (Windows)

## Step 1: Activate Virtual Environment

First, make sure you're in the project directory and activate the virtual environment:

```powershell
# Navigate to your project directory
cd C:\Users\vyome\phil-ideas\philanthropic-ideas

# Activate the virtual environment
.\.venv\Scripts\Activate.ps1
```

You should see `(.venv)` at the beginning of your command prompt.

## Step 2: Verify Python Environment

Check that you're using the correct Python:

```powershell
# Check Python executable
python -c "import sys; print('Python executable:', sys.executable)"

# Check Python version
python --version
```

You should see something like:
```
Python executable: C:\Users\vyome\phil-ideas\philanthropic-ideas\.venv\Scripts\python.exe
Python 3.12.x
```

## Step 3: Install Dependencies

Upgrade pip and install dependencies:

```powershell
# Upgrade pip, setuptools, and wheel
python -m pip install --upgrade pip setuptools wheel

# Install PyTorch for CPU (Python 3.12)
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install all other dependencies
python -m pip install -r requirements.txt
```

## Step 4: Verify Installation

Test that key packages are installed:

```powershell
# Test core packages
python -c "import fastapi, sqlalchemy, pandas, numpy; print('✅ Core packages installed')"

# Test version attributes (note the double underscores)
python -c "import sqlalchemy, ratelimit; print(f'SQLAlchemy: {sqlalchemy.__version__}'); print(f'RateLimit: {ratelimit.__version__}')"
```

## Step 5: Database Validation

Run the database validation script:

```powershell
# Run database tests
python test_database.py
```

This will test:
- Database connection
- Table creation
- Basic CRUD operations
- Database relationships
- JSON field operations

## Step 6: Environment Setup

Create your `.env` file:

```powershell
# Copy the template
copy env_template.txt .env
```

Edit `.env` and add your API keys:
```
OPENALEX_API_KEY=your_actual_key_here
SEMANTIC_SCHOLAR_API_KEY=your_actual_key_here
CRUNCHBASE_API_KEY=your_actual_key_here
GOOGLE_API_KEY=your_actual_key_here
NIH_API_KEY=your_actual_key_here
```

## Step 7: Test the Application

Run the main application:

```powershell
# Start the application
python run.py
```

Choose option 1 to start the API server, then visit:
- API: http://localhost:8000
- Web Interface: http://localhost:8000/web

## Troubleshooting

### Issue: "No module named 'fastapi'"
**Solution**: Make sure you're in the activated virtual environment (see `.venv` in prompt)

### Issue: "No module named 'sqlalchemy'"
**Solution**: Install dependencies in the activated venv:
```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Issue: Package installation errors
**Solution**: Install packages one by one to identify the problematic one:
```powershell
python -m pip install fastapi
python -m pip install sqlalchemy
python -m pip install pandas
# etc.
```

### Issue: Python version conflicts
**Solution**: Ensure you're using Python 3.12 and install compatible versions:
```powershell
python --version  # Should show 3.12.x
```

## Database Schema Overview

The database includes these main tables:

1. **data_sources** - Tracks API sources and their metadata
2. **raw_data** - Stores ingested data from various sources
3. **extracted_ideas** - Philanthropic ideas extracted from raw data
4. **idea_evaluations** - Detailed evaluations of ideas
5. **talent_profiles** - Identified potential talent
6. **idea_talent_matches** - Matches between ideas and talent
7. **analysis_runs** - Tracks analysis execution
8. **benchmark_interventions** - Benchmark data for comparison
9. **search_queries** - Logs of search operations

## Next Steps

After successful setup:
1. Add your API keys to `.env`
2. Run data ingestion: `python -m data_ingestion.main`
3. Extract ideas: `python -m analysis.idea_extractor`
4. Evaluate ideas: `python -m scoring.idea_evaluator`
5. Identify talent: `python -m scoring.talent_identifier`

## Support

If you encounter issues:
1. Check that you're in the activated virtual environment
2. Verify Python version is 3.12
3. Ensure all dependencies are installed
4. Check the database validation script output
