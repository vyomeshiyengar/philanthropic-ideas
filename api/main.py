"""
FastAPI application for the Philanthropic Ideas Generator.
"""
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import asyncio

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from storage.database import get_db, init_database, db_manager
from storage.cache import api_cache
from data_ingestion.main import DataIngestionOrchestrator
from analysis.idea_extractor import IdeaExtractor
from scoring.idea_evaluator import IdeaEvaluator
from scoring.talent_identifier import TalentIdentifier

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Philanthropic Ideas Generator",
    description="A comprehensive system for identifying and evaluating high-impact philanthropic opportunities",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="web_interface"), name="static")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")

# Pydantic models for API requests/responses
class IngestionRequest(BaseModel):
    domains: Optional[List[str]] = None
    sources: Optional[List[str]] = None
    max_results_per_keyword: int = 50

class ExtractionRequest(BaseModel):
    domain: Optional[str] = None
    confidence_threshold: float = 0.3

class EvaluationRequest(BaseModel):
    domain: Optional[str] = None
    evaluator: str = "automated"

class TalentRequest(BaseModel):
    idea_id: Optional[int] = None
    candidates_per_idea: int = 2

class IdeaResponse(BaseModel):
    idea_id: int
    title: str
    description: str
    domain: str
    primary_metric: str
    idea_type: str
    overall_score: Optional[float] = None
    impact_score: Optional[float] = None
    neglectedness_score: Optional[float] = None
    tractability_score: Optional[float] = None
    scalability_score: Optional[float] = None
    benchmark_comparison: Optional[Dict[str, Any]] = None

class TalentResponse(BaseModel):
    talent_id: int
    name: str
    title: str
    organization: str
    location: str
    expertise_areas: List[str]
    experience_years: int
    education: List[str]
    fit_score: float
    match_reasoning: str
    potential_role: str
    source: str
    source_url: str

# Global instances
ingestion_orchestrator = None
idea_extractor = None
idea_evaluator = None
talent_identifier = None

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    global ingestion_orchestrator, idea_extractor, idea_evaluator, talent_identifier
    
    # Initialize database
    init_database()
    
    # Initialize components
    ingestion_orchestrator = DataIngestionOrchestrator()
    idea_extractor = IdeaExtractor()
    idea_evaluator = IdeaEvaluator()
    talent_identifier = TalentIdentifier()
    
    logger.info("Philanthropic Ideas Generator API started successfully")

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Philanthropic Ideas Generator API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/web")
async def web_interface():
    """Serve the web interface."""
    return FileResponse("web_interface/index.html")

@app.get("/web_interface/index.html")
async def web_interface_legacy():
    """Serve the web interface (legacy path)."""
    return FileResponse("web_interface/index.html")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "database": "connected",
            "ingestion": "ready",
            "analysis": "ready",
            "scoring": "ready",
            "talent": "ready"
        }
    }

# Data Ingestion Endpoints
@app.post("/ingestion/run")
async def run_ingestion(request: IngestionRequest, background_tasks: BackgroundTasks):
    """Run data ingestion from all sources."""
    try:
        # Run ingestion in background
        background_tasks.add_task(
            ingestion_orchestrator.run_full_ingestion,
            domains=request.domains
        )
        
        return {
            "message": "Data ingestion started in background",
            "domains": request.domains,
            "max_results_per_keyword": request.max_results_per_keyword
        }
    except Exception as e:
        logger.error(f"Failed to start ingestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingestion/source/{source_name}")
async def run_source_ingestion(source_name: str, request: IngestionRequest, 
                             background_tasks: BackgroundTasks):
    """Run data ingestion for a specific source."""
    try:
        # Run ingestion in background
        background_tasks.add_task(
            ingestion_orchestrator.run_source_ingestion,
            source_name=source_name,
            domains=request.domains
        )
        
        return {
            "message": f"Data ingestion for {source_name} started in background",
            "source": source_name,
            "domains": request.domains
        }
    except Exception as e:
        logger.error(f"Failed to start {source_name} ingestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ingestion/status/{run_id}")
async def get_ingestion_status(run_id: int):
    """Get the status of an ingestion run."""
    try:
        status = ingestion_orchestrator.get_ingestion_status(run_id)
        if not status:
            raise HTTPException(status_code=404, detail="Ingestion run not found")
        return status
    except Exception as e:
        logger.error(f"Failed to get ingestion status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Idea Extraction Endpoints
@app.post("/extraction/extract")
async def extract_ideas(request: ExtractionRequest, background_tasks: BackgroundTasks):
    """Extract ideas from raw data."""
    try:
        # Extract ideas in background
        background_tasks.add_task(
            _extract_ideas_background,
            domain=request.domain,
            confidence_threshold=request.confidence_threshold
        )
        
        return {
            "message": "Idea extraction started in background",
            "domain": request.domain,
            "confidence_threshold": request.confidence_threshold
        }
    except Exception as e:
        logger.error(f"Failed to start idea extraction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _extract_ideas_background(domain: Optional[str], confidence_threshold: float):
    """Background task for idea extraction."""
    try:
        # Extract ideas
        ideas = idea_extractor.extract_ideas_from_raw_data(domain=domain)
        
        # Filter by confidence threshold
        filtered_ideas = [idea for idea in ideas if idea.get("confidence_score", 0) >= confidence_threshold]
        
        # Save ideas
        saved_count = idea_extractor.save_extracted_ideas(filtered_ideas)
        
        logger.info(f"Extracted and saved {saved_count} ideas")
        
    except Exception as e:
        logger.error(f"Background idea extraction failed: {e}")

@app.get("/extraction/ideas", response_model=List[IdeaResponse])
async def get_extracted_ideas(domain: Optional[str] = None, limit: int = 100, 
                            db: Session = Depends(get_db)):
    """Get extracted ideas."""
    try:
        from storage.models import ExtractedIdea
        
        query = db.query(ExtractedIdea)
        if domain:
            query = query.filter(ExtractedIdea.domain == domain)
        
        ideas = query.order_by(ExtractedIdea.created_at.desc()).limit(limit).all()
        
        return [
            IdeaResponse(
                idea_id=idea.id,
                title=idea.title,
                description=idea.description,
                domain=idea.domain,
                primary_metric=idea.primary_metric,
                idea_type=idea.idea_type
            )
            for idea in ideas
        ]
    except Exception as e:
        logger.error(f"Failed to get extracted ideas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Evaluation Endpoints
@app.post("/evaluation/evaluate")
async def evaluate_ideas(request: EvaluationRequest, background_tasks: BackgroundTasks):
    """Evaluate all ideas."""
    try:
        # Run evaluation in background
        background_tasks.add_task(
            _evaluate_ideas_background,
            domain=request.domain,
            evaluator=request.evaluator
        )
        
        return {
            "message": "Idea evaluation started in background",
            "domain": request.domain,
            "evaluator": request.evaluator
        }
    except Exception as e:
        logger.error(f"Failed to start idea evaluation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _evaluate_ideas_background(domain: Optional[str], evaluator: str):
    """Background task for idea evaluation."""
    try:
        results = idea_evaluator.evaluate_all_ideas(domain=domain, evaluator=evaluator)
        logger.info(f"Evaluated {results.get('evaluated', 0)} ideas")
        
    except Exception as e:
        logger.error(f"Background idea evaluation failed: {e}")

@app.get("/evaluation/top-ideas", response_model=List[IdeaResponse])
async def get_top_ideas(domain: Optional[str] = None, metric: Optional[str] = None, 
                       limit: int = 10):
    """Get top-scoring ideas."""
    try:
        ideas = idea_evaluator.get_top_ideas(domain=domain, metric=metric, limit=limit)
        
        return [
            IdeaResponse(
                idea_id=idea["idea_id"],
                title=idea["title"],
                description=idea["description"],
                domain=idea["domain"],
                primary_metric=idea["primary_metric"],
                idea_type=idea["idea_type"],
                overall_score=idea["overall_score"],
                impact_score=idea["impact_score"],
                neglectedness_score=idea["neglectedness_score"],
                tractability_score=idea["tractability_score"],
                scalability_score=idea["scalability_score"],
                benchmark_comparison=idea["benchmark_comparison"]
            )
            for idea in ideas
        ]
    except Exception as e:
        logger.error(f"Failed to get top ideas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/evaluation/contrarian")
async def get_contrarian_ranking(domain: Optional[str] = None):
    """Get contrarian ranking of ideas."""
    try:
        ideas = idea_evaluator.generate_contrarian_ranking(domain=domain)
        return ideas
    except Exception as e:
        logger.error(f"Failed to get contrarian ranking: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Talent Identification Endpoints
@app.post("/talent/identify")
async def identify_talent(request: TalentRequest, background_tasks: BackgroundTasks):
    """Identify talent for ideas."""
    try:
        if request.idea_id:
            # Identify talent for specific idea
            background_tasks.add_task(
                _identify_talent_for_idea_background,
                idea_id=request.idea_id,
                candidates_per_idea=request.candidates_per_idea
            )
            
            return {
                "message": f"Talent identification for idea {request.idea_id} started in background",
                "idea_id": request.idea_id,
                "candidates_per_idea": request.candidates_per_idea
            }
        else:
            # Identify talent for top ideas
            top_ideas = idea_evaluator.get_top_ideas(limit=5)
            
            background_tasks.add_task(
                _identify_talent_for_top_ideas_background,
                top_ideas=top_ideas,
                candidates_per_idea=request.candidates_per_idea
            )
            
            return {
                "message": "Talent identification for top ideas started in background",
                "top_ideas_count": len(top_ideas),
                "candidates_per_idea": request.candidates_per_idea
            }
    except Exception as e:
        logger.error(f"Failed to start talent identification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _identify_talent_for_idea_background(idea_id: int, candidates_per_idea: int):
    """Background task for talent identification for specific idea."""
    try:
        candidates = await talent_identifier.identify_talent_for_idea(idea_id, candidates_per_idea)
        logger.info(f"Identified {len(candidates)} talent candidates for idea {idea_id}")
        
    except Exception as e:
        logger.error(f"Background talent identification failed: {e}")

async def _identify_talent_for_top_ideas_background(top_ideas: List[Dict[str, Any]], 
                                                  candidates_per_idea: int):
    """Background task for talent identification for top ideas."""
    try:
        results = await talent_identifier.identify_talent_for_top_ideas(top_ideas, candidates_per_idea)
        logger.info(f"Identified talent for {results['ideas_with_talent']} ideas")
        
    except Exception as e:
        logger.error(f"Background talent identification failed: {e}")

@app.get("/talent/idea/{idea_id}", response_model=List[TalentResponse])
async def get_talent_for_idea(idea_id: int):
    """Get talent profiles for a specific idea."""
    try:
        talent = talent_identifier.get_talent_for_idea(idea_id)
        
        return [
            TalentResponse(
                talent_id=t["talent_id"],
                name=t["name"],
                title=t["title"],
                organization=t["organization"],
                location=t["location"],
                expertise_areas=t["expertise_areas"],
                experience_years=t["experience_years"],
                education=t["education"],
                fit_score=t["fit_score"],
                match_reasoning=t["match_reasoning"],
                potential_role=t["potential_role"],
                source=t["source"],
                source_url=t["source_url"]
            )
            for t in talent
        ]
    except Exception as e:
        logger.error(f"Failed to get talent for idea {idea_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/talent/search")
async def search_talent_by_expertise(expertise: str, max_results: int = 10):
    """Search for talent by expertise area."""
    try:
        talent = talent_identifier.search_talent_by_expertise(expertise, max_results)
        return talent
    except Exception as e:
        logger.error(f"Failed to search talent by expertise: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/talent/statistics")
async def get_talent_statistics():
    """Get statistics about talent profiles."""
    try:
        stats = talent_identifier.get_talent_statistics()
        return stats
    except Exception as e:
        logger.error(f"Failed to get talent statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Combined Workflow Endpoints
@app.post("/workflow/full-pipeline")
async def run_full_pipeline(background_tasks: BackgroundTasks):
    """Run the full pipeline: ingestion -> extraction -> evaluation -> talent identification."""
    try:
        # Run full pipeline in background
        background_tasks.add_task(_run_full_pipeline_background)
        
        return {
            "message": "Full pipeline started in background",
            "steps": ["ingestion", "extraction", "evaluation", "talent_identification"]
        }
    except Exception as e:
        logger.error(f"Failed to start full pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Prototype-specific endpoints
@app.post("/prototype/run")
async def run_prototype_pipeline(background_tasks: BackgroundTasks):
    """Run the prototype pipeline: OpenAlex + NIH RePORTER + Web Scraper -> extraction -> evaluation -> talent identification."""
    try:
        # Run prototype pipeline in background
        background_tasks.add_task(_run_prototype_pipeline_background)
        
        return {
            "message": "Prototype pipeline started in background",
            "steps": ["prototype_ingestion", "extraction", "evaluation", "talent_identification"],
            "sources": ["openalex", "nih_reporter", "web_scraper"]
        }
    except Exception as e:
        logger.error(f"Failed to start prototype pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _run_prototype_pipeline_background():
    """Background task for prototype pipeline."""
    try:
        logger.info("Starting prototype pipeline...")
        
        # Step 1: Prototype data ingestion (only enabled sources)
        logger.info("Step 1: Running prototype data ingestion...")
        ingestion_results = await ingestion_orchestrator.run_full_ingestion()
        logger.info(f"Prototype ingestion completed: {ingestion_results['summary']['total_successful']} items")
        
        # Step 2: Idea extraction
        logger.info("Step 2: Running idea extraction...")
        ideas = idea_extractor.extract_ideas_from_raw_data()
        saved_count = idea_extractor.save_extracted_ideas(ideas)
        logger.info(f"Extraction completed: {saved_count} ideas saved")
        
        # Step 3: Idea evaluation
        logger.info("Step 3: Running idea evaluation...")
        evaluation_results = idea_evaluator.evaluate_all_ideas()
        logger.info(f"Evaluation completed: {evaluation_results['evaluated']} ideas evaluated")
        
        # Step 4: Talent identification
        logger.info("Step 4: Running talent identification...")
        top_ideas = idea_evaluator.get_top_ideas(limit=5)
        talent_results = await talent_identifier.identify_talent_for_top_ideas(top_ideas)
        logger.info(f"Talent identification completed: {talent_results['total_candidates']} candidates")
        
        logger.info("Prototype pipeline completed successfully!")
        
    except Exception as e:
        logger.error(f"Prototype pipeline failed: {e}")

@app.get("/prototype/status")
async def get_prototype_status(db: Session = Depends(get_db)):
    """Get the current status of prototype data and ideas."""
    try:
        from storage.models import RawData, ExtractedIdea, IdeaEvaluation, DataSource
        
        # Get data source statistics
        sources = db.query(DataSource).filter(DataSource.status == "active").all()
        source_stats = {}
        for source in sources:
            count = db.query(RawData).filter(RawData.data_source_id == source.id).count()
            source_stats[source.name] = count
        
        # Get idea statistics
        total_ideas = db.query(ExtractedIdea).count()
        evaluated_ideas = db.query(IdeaEvaluation).count()
        
        # Get top ideas
        top_ideas = idea_evaluator.get_top_ideas(limit=5) if evaluated_ideas > 0 else []
        
        return {
            "data_sources": source_stats,
            "total_raw_data": sum(source_stats.values()),
            "total_ideas": total_ideas,
            "evaluated_ideas": evaluated_ideas,
            "top_ideas": top_ideas
        }
    except Exception as e:
        logger.error(f"Failed to get prototype status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/prototype/raw-data")
async def get_prototype_raw_data(limit: int = 50, db: Session = Depends(get_db)):
    """Get raw data from prototype sources."""
    try:
        from storage.models import RawData, DataSource
        
        # Get active sources
        active_sources = db.query(DataSource).filter(DataSource.status == "active").all()
        source_ids = [source.id for source in active_sources]
        
        # Get raw data from active sources, filtering out poor quality data
        raw_data = db.query(RawData).filter(
            RawData.data_source_id.in_(source_ids),
            RawData.title != "...",  # Filter out empty titles
            RawData.title != "",     # Filter out empty titles
            RawData.title.isnot(None),  # Filter out null titles
            RawData.full_text.isnot(None),  # Filter out null content
            RawData.full_text != "",  # Filter out empty content
            RawData.full_text != "...",  # Filter out placeholder content
            RawData.full_text != "No content available",  # Filter out placeholder content
        ).order_by(RawData.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": data.id,
                "source_name": data.data_source.name,
                "title": data.title,
                "content": data.full_text[:300] + "..." if data.full_text and len(data.full_text) > 300 else (data.full_text or ""),
                "url": data.url,
                "created_at": data.created_at.isoformat(),
                "metadata": data.metadata_json
            }
            for data in raw_data
        ]
    except Exception as e:
        logger.error(f"Failed to get prototype raw data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/prototype/ideas")
async def get_prototype_ideas(limit: int = 20, db: Session = Depends(get_db)):
    """Get extracted ideas from prototype data."""
    try:
        from storage.models import ExtractedIdea
        
        # Get ideas, filtering out low quality ones and ordering by confidence
        ideas = db.query(ExtractedIdea).filter(
            ExtractedIdea.title != "...",  # Filter out empty titles
            ExtractedIdea.title != "",     # Filter out empty titles
            ExtractedIdea.title.isnot(None),  # Filter out null titles
            ExtractedIdea.confidence_score >= 0.3,  # Filter out very low confidence ideas
            # Filter out generic titles
            ~ExtractedIdea.title.like("The % for %"),  # "The X for Y" pattern
            ~ExtractedIdea.title.like("% for %"),      # "X for Y" pattern
            ~ExtractedIdea.title.like("% % %"),        # Very generic patterns
        ).order_by(
            ExtractedIdea.confidence_score.desc(),  # Order by confidence first
            ExtractedIdea.created_at.desc()         # Then by recency
        ).limit(limit).all()
        
        return [
            {
                "id": idea.id,
                "title": idea.title,
                "description": idea.description,
                "domain": idea.domain,
                "primary_metric": idea.primary_metric,
                "idea_type": idea.idea_type,
                "confidence_score": idea.confidence_score,
                "created_at": idea.created_at.isoformat(),
                "thought_process": idea.thought_process
            }
            for idea in ideas
        ]
    except Exception as e:
        logger.error(f"Failed to get prototype ideas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _run_full_pipeline_background():
    """Background task for full pipeline."""
    try:
        logger.info("Starting full pipeline...")
        
        # Step 1: Data ingestion
        logger.info("Step 1: Running data ingestion...")
        ingestion_results = await ingestion_orchestrator.run_full_ingestion()
        logger.info(f"Ingestion completed: {ingestion_results['summary']['total_successful']} items")
        
        # Step 2: Idea extraction
        logger.info("Step 2: Running idea extraction...")
        ideas = idea_extractor.extract_ideas_from_raw_data()
        saved_count = idea_extractor.save_extracted_ideas(ideas)
        logger.info(f"Extraction completed: {saved_count} ideas saved")
        
        # Step 3: Idea evaluation
        logger.info("Step 3: Running idea evaluation...")
        evaluation_results = idea_evaluator.evaluate_all_ideas()
        logger.info(f"Evaluation completed: {evaluation_results['evaluated']} ideas evaluated")
        
        # Step 4: Talent identification
        logger.info("Step 4: Running talent identification...")
        top_ideas = idea_evaluator.get_top_ideas(limit=5)
        talent_results = await talent_identifier.identify_talent_for_top_ideas(top_ideas)
        logger.info(f"Talent identification completed: {talent_results['total_candidates']} candidates")
        
        logger.info("Full pipeline completed successfully!")
        
    except Exception as e:
        logger.error(f"Full pipeline failed: {e}")

# Statistics Endpoints
@app.get("/statistics/overview")
async def get_system_statistics(db: Session = Depends(get_db)):
    """Get overview statistics of the system."""
    try:
        from storage.models import RawData, ExtractedIdea, IdeaEvaluation, TalentProfile
        
        stats = {
            "raw_data": db.query(RawData).count(),
            "extracted_ideas": db.query(ExtractedIdea).count(),
            "evaluated_ideas": db.query(IdeaEvaluation).count(),
            "talent_profiles": db.query(TalentProfile).count(),
            "domains": {},
            "metrics": {}
        }
        
        # Count by domain
        for idea in db.query(ExtractedIdea.domain).distinct():
            count = db.query(ExtractedIdea).filter(ExtractedIdea.domain == idea[0]).count()
            stats["domains"][idea[0]] = count
        
        # Count by metric
        for idea in db.query(ExtractedIdea.primary_metric).distinct():
            count = db.query(ExtractedIdea).filter(ExtractedIdea.primary_metric == idea[0]).count()
            stats["metrics"][idea[0]] = count
        
        return stats
    except Exception as e:
        logger.error(f"Failed to get system statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Cache management endpoints
@app.get("/cache/stats")
async def get_cache_statistics():
    """Get cache statistics."""
    try:
        return api_cache.get_stats()
    except Exception as e:
        logger.error(f"Error getting cache statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/cache/clear")
async def clear_cache(source: Optional[str] = None):
    """Clear cache entries."""
    try:
        cleared_count = api_cache.clear(source)
        return {"message": f"Cleared {cleared_count} cache entries", "cleared_count": cleared_count}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/cache/invalidate")
async def invalidate_cache(source: str, query: str):
    """Invalidate a specific cache entry."""
    try:
        success = api_cache.invalidate(source, query)
        if success:
            return {"message": f"Invalidated cache for {source}:{query}"}
        else:
            return {"message": f"No cache entry found for {source}:{query}"}
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
