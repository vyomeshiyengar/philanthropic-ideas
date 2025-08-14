"""
Configuration settings for the Philanthropic Ideas Generator.
"""
from pydantic_settings import BaseSettings
from typing import List, Dict, Optional
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    DATABASE_URL: str = "sqlite:///./philanthropic_ideas.db"
    REDIS_URL: str = "redis://localhost:6379"
    
    # API Keys (set these in .env file)
    OPENALEX_API_KEY: Optional[str] = None
    SEMANTIC_SCHOLAR_API_KEY: Optional[str] = None
    CRUNCHBASE_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    GOOGLE_CUSTOM_SEARCH_ENGINE_ID: Optional[str] = None
    NIH_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    
    # Rate limiting
    OPENALEX_RATE_LIMIT: int = 100  # requests per hour
    SEMANTIC_SCHOLAR_RATE_LIMIT: int = 100
    CRUNCHBASE_RATE_LIMIT: int = 1000
    GOOGLE_RATE_LIMIT: int = 100
    
    # Data sources configuration
    DATA_SOURCES: Dict[str, Dict] = {
        "openalex": {
            "base_url": "https://api.openalex.org",
            "search_endpoint": "/works",
            "enabled": True,
            "requires_auth": False  # OpenAlex doesn't require authentication
        },
        "pubmed": {
            "base_url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
            "search_endpoint": "/esearch.fcgi",
            "fetch_endpoint": "/efetch.fcgi",
            "enabled": False  # Disabled for prototype
        },
        "semantic_scholar": {
            "base_url": "https://api.semanticscholar.org",
            "search_endpoint": "/graph/v1/paper/search",
            "enabled": False  # Disabled for prototype
        },
        "world_bank": {
            "base_url": "https://api.worldbank.org",
            "indicators_endpoint": "/v2/country/all/indicator",
            "projects_endpoint": "/v2/projects",
            "enabled": False  # Disabled for prototype
        },
        "nih_reporter": {
            "base_url": "https://api.reporter.nih.gov",
            "search_endpoint": "/v2/projects/search",
            "enabled": True,
            "requires_auth": False  # NIH RePORTER doesn't require authentication
        },
        "cordis": {
            "base_url": "https://cordis.europa.eu",
            "projects_endpoint": "/projects",
            "enabled": False  # Disabled for prototype
        }
    }
    
    # Expert blogs and sources (removed problematic Substack sources that cause infinite loops)
    EXPERT_SOURCES: List[Dict] = [
        {"name": "Dwarkesh Patel", "url": "https://www.dwarkeshpatel.com", "type": "blog"},
        {"name": "Astral Codex Ten", "url": "https://www.astralcodexten.com", "type": "blog"},
        {"name": "Open Philanthropy", "url": "https://www.openphilanthropy.org", "type": "organization"},
        {"name": "Rethink Priorities", "url": "https://rethinkpriorities.org", "type": "organization"},
        {"name": "EA Forum", "url": "https://forum.effectivealtruism.org", "type": "forum"},
        {"name": "Michael Nielsen", "url": "https://michaelnielsen.org", "type": "blog"},
        {"name": "Jacob Trefethen", "url": "https://trefethen.medium.com", "type": "blog"},
        {"name": "Wild Animal Initiative", "url": "https://wildanimalinitiative.org/research", "type": "organization"},
        {"name": "Statecraft", "url": "https://www.statecraft.pub", "type": "blog"},
        {"name": "Slow Boring", "url": "https://www.slowboring.com", "type": "blog"},
        {"name": "Asterisk Magazine", "url": "https://asteriskmag.com", "type": "magazine"},
        {"name": "Asimov Press", "url": "https://asimov.press", "type": "publisher"},
        {"name": "The Great Gender Divergence", "url": "https://thegreatgenderdivergence.com", "type": "blog"},
        {"name": "Devon Zuegel", "url": "https://devonzuegel.com", "type": "blog"},
        {"name": "Center for Global Development", "url": "https://www.cgdev.org", "type": "organization"},
        {"name": "Lant Pritchett", "url": "https://lantpritchett.org", "type": "blog"},
        {"name": "Gwern", "url": "https://www.gwern.net", "type": "blog"},
        {"name": "Animal Charity Evaluators", "url": "https://animalcharityevaluators.org", "type": "organization"}
    ]
    
    # Benchmark interventions
    BENCHMARKS: Dict[str, Dict] = {
        "dalys": {
            "name": "GiveWell",
            "url": "https://givewell.org",
            "cost_per_daly": 100,  # USD per DALY averted
            "description": "Health interventions benchmark"
        },
        "walys": {
            "name": "The Humane League",
            "url": "https://thehumaneleague.org",
            "cost_per_waly": 50,  # USD per WALY averted
            "description": "Animal welfare benchmark"
        },
        "welbys": {
            "name": "StrongMinds",
            "url": "https://strongminds.org",
            "cost_per_welby": 200,  # USD per WELBY averted
            "description": "Wellbeing interventions benchmark"
        },
        "log_income": {
            "name": "GiveDirectly",
            "url": "https://givedirectly.org",
            "cost_per_income_increase": 1000,  # USD per log income increase
            "description": "Economic development benchmark"
        },
        "co2": {
            "name": "Carbon Removal",
            "url": "https://carbonremoval.org",
            "cost_per_ton_co2": 100,  # USD per ton CO2 removed
            "description": "Climate interventions benchmark"
        }
    }
    
    # Scoring weights
    SCORING_WEIGHTS: Dict[str, float] = {
        "impact": 0.4,
        "neglectedness": 0.3,
        "tractability": 0.2,
        "scalability": 0.1
    }
    
    # Neglectedness thresholds (annual funding in USD)
    NEGLECTEDNESS_THRESHOLDS: Dict[str, float] = {
        "highly_neglected": 1000000,  # < $1M
        "moderately_neglected": 10000000,  # < $10M
        "somewhat_neglected": 100000000,  # < $100M
        "well_funded": float('inf')
    }
    
    # Search keywords for different domains
    SEARCH_KEYWORDS: Dict[str, List[str]] = {
        "health": [
            "public health", "disease prevention", "vaccination", "maternal health",
            "child mortality", "malaria", "tuberculosis", "HIV", "nutrition"
        ],
        "education": [
            "education", "learning", "pedagogy", "schooling", "literacy",
            "early childhood", "teacher training", "educational technology"
        ],
        "economic_development": [
            "economic development", "poverty reduction", "income generation",
            "microfinance", "entrepreneurship", "job creation", "skills training"
        ],
        "animal_welfare": [
            "animal welfare", "farmed animals", "wild animals", "animal rights",
            "livestock", "fishing", "animal suffering"
        ],
        "climate": [
            "climate change", "carbon removal", "renewable energy", "emissions reduction",
            "adaptation", "mitigation", "sustainability"
        ],
        "wellbeing": [
            "mental health", "happiness", "life satisfaction", "psychological wellbeing",
            "depression", "anxiety", "social connection"
        ]
    }
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields from environment


# Global settings instance
settings = Settings()
