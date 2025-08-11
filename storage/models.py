"""
Database models for the Philanthropic Ideas Generator.
"""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, List, Dict, Any

Base = declarative_base()


class DataSource(Base):
    """Model for tracking data sources and their metadata."""
    __tablename__ = "data_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    source_type = Column(String(100), nullable=False)  # api, web_scrape, manual
    url = Column(String(500), nullable=True)
    api_key_required = Column(Boolean, default=False)
    rate_limit = Column(Integer, nullable=True)
    last_accessed = Column(DateTime, default=func.now())
    status = Column(String(50), default="active")  # active, inactive, error
    metadata_json = Column(JSON, nullable=True)
    
    # Relationships
    raw_data = relationship("RawData", back_populates="data_source")


class RawData(Base):
    """Model for storing raw data from various sources."""
    __tablename__ = "raw_data"
    
    id = Column(Integer, primary_key=True, index=True)
    data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False)
    content_type = Column(String(100), nullable=False)  # paper, article, project, indicator
    title = Column(String(500), nullable=True)
    authors = Column(JSON, nullable=True)  # List of author names
    abstract = Column(Text, nullable=True)
    full_text = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)
    publication_date = Column(DateTime, nullable=True)
    keywords = Column(JSON, nullable=True)  # List of keywords
    metadata_json = Column(JSON, nullable=True)  # Additional metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    data_source = relationship("DataSource", back_populates="raw_data")
    extracted_ideas = relationship("ExtractedIdea", back_populates="raw_data")


class ExtractedIdea(Base):
    """Model for storing ideas extracted from raw data."""
    __tablename__ = "extracted_ideas"
    
    id = Column(Integer, primary_key=True, index=True)
    raw_data_id = Column(Integer, ForeignKey("raw_data.id"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    domain = Column(String(100), nullable=False)  # health, education, economic_development, etc.
    primary_metric = Column(String(50), nullable=False)  # dalys, walys, log_income, co2, welbys
    idea_type = Column(String(50), nullable=False)  # newly_viable, evergreen
    confidence_score = Column(Float, nullable=True)  # 0-1 confidence in extraction
    extraction_method = Column(String(100), nullable=False)  # nlp, manual, hybrid
    thought_process = Column(Text, nullable=True)  # Explanation of extraction reasoning
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    raw_data = relationship("RawData", back_populates="extracted_ideas")
    evaluations = relationship("IdeaEvaluation", back_populates="idea")


class IdeaEvaluation(Base):
    """Model for storing detailed evaluations of ideas."""
    __tablename__ = "idea_evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("extracted_ideas.id"), nullable=False)
    
    # Impact scores (0-10 scale)
    impact_score = Column(Float, nullable=False)
    impact_confidence = Column(Float, nullable=True)  # 0-1 confidence in impact estimate
    impact_notes = Column(Text, nullable=True)
    
    # Neglectedness scores
    neglectedness_score = Column(Float, nullable=False)  # 0-10 scale
    annual_funding_estimate = Column(Float, nullable=True)  # USD
    neglectedness_notes = Column(Text, nullable=True)
    
    # Tractability scores
    tractability_score = Column(Float, nullable=False)  # 0-10 scale
    tractability_notes = Column(Text, nullable=True)
    
    # Scalability scores
    scalability_score = Column(Float, nullable=False)  # 0-10 scale
    scalability_notes = Column(Text, nullable=True)
    
    # Overall scores
    overall_score = Column(Float, nullable=False)
    benchmark_comparison = Column(JSON, nullable=True)  # Comparison with benchmark interventions
    
    # Evaluation metadata
    evaluator = Column(String(255), nullable=True)  # Who performed the evaluation
    evaluation_date = Column(DateTime, default=func.now())
    evaluation_method = Column(String(100), nullable=False)  # manual, automated, hybrid
    
    # Relationships
    idea = relationship("ExtractedIdea", back_populates="evaluations")


class TalentProfile(Base):
    """Model for storing identified talent profiles."""
    __tablename__ = "talent_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    organization = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    twitter_url = Column(String(500), nullable=True)
    website = Column(String(500), nullable=True)
    
    # Background and experience
    background = Column(Text, nullable=True)
    expertise_areas = Column(JSON, nullable=True)  # List of expertise areas
    experience_years = Column(Integer, nullable=True)
    education = Column(JSON, nullable=True)  # List of degrees/institutions
    
    # Source information
    source = Column(String(100), nullable=False)  # crunchbase, web_search, manual
    source_url = Column(String(500), nullable=True)
    confidence_score = Column(Float, nullable=True)  # 0-1 confidence in profile accuracy
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class IdeaTalentMatch(Base):
    """Model for matching ideas with potential talent."""
    __tablename__ = "idea_talent_matches"
    
    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("extracted_ideas.id"), nullable=False)
    talent_id = Column(Integer, ForeignKey("talent_profiles.id"), nullable=False)
    
    # Match quality scores
    fit_score = Column(Float, nullable=False)  # 0-10 how well they fit the idea
    experience_relevance = Column(Float, nullable=True)  # 0-10 relevance of their experience
    background_relevance = Column(Float, nullable=True)  # 0-10 relevance of their background
    
    # Match details
    match_reasoning = Column(Text, nullable=True)  # Why this person is a good fit
    potential_role = Column(String(255), nullable=True)  # What role they might play
    
    created_at = Column(DateTime, default=func.now())


class AnalysisRun(Base):
    """Model for tracking analysis runs and their results."""
    __tablename__ = "analysis_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    run_name = Column(String(255), nullable=False)
    run_type = Column(String(100), nullable=False)  # data_ingestion, idea_extraction, evaluation, talent_matching
    
    # Run parameters
    parameters = Column(JSON, nullable=True)  # Parameters used for this run
    data_sources_used = Column(JSON, nullable=True)  # List of data sources used
    
    # Run results
    status = Column(String(50), default="running")  # running, completed, failed
    start_time = Column(DateTime, default=func.now())
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Results summary
    items_processed = Column(Integer, default=0)
    items_successful = Column(Integer, default=0)
    items_failed = Column(Integer, default=0)
    error_log = Column(Text, nullable=True)
    
    # Output files
    output_files = Column(JSON, nullable=True)  # List of output file paths


class BenchmarkIntervention(Base):
    """Model for storing benchmark interventions for comparison."""
    __tablename__ = "benchmark_interventions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    organization = Column(String(255), nullable=True)
    url = Column(String(500), nullable=True)
    
    # Intervention details
    primary_metric = Column(String(50), nullable=False)  # dalys, walys, log_income, co2, welbys
    cost_per_unit = Column(Float, nullable=False)  # Cost per unit of impact
    unit_description = Column(String(255), nullable=True)  # Description of the unit
    
    # Effectiveness data
    effectiveness_estimate = Column(Float, nullable=True)  # Point estimate
    effectiveness_ci_lower = Column(Float, nullable=True)  # Confidence interval lower
    effectiveness_ci_upper = Column(Float, nullable=True)  # Confidence interval upper
    
    # Additional metadata
    description = Column(Text, nullable=True)
    evidence_quality = Column(String(50), nullable=True)  # high, medium, low
    last_updated = Column(DateTime, default=func.now())
    source = Column(String(255), nullable=True)  # Where this benchmark data comes from


class SearchQuery(Base):
    """Model for tracking search queries and their results."""
    __tablename__ = "search_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(String(500), nullable=False)
    data_source = Column(String(100), nullable=False)
    domain = Column(String(100), nullable=True)  # health, education, etc.
    
    # Query results
    results_count = Column(Integer, default=0)
    successful = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Timing
    query_time = Column(DateTime, default=func.now())
    duration_seconds = Column(Float, nullable=True)
    
    # Rate limiting
    rate_limit_remaining = Column(Integer, nullable=True)
    rate_limit_reset_time = Column(DateTime, nullable=True)
