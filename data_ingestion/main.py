"""
Main data ingestion orchestrator for the Philanthropic Ideas Generator.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from config.settings import settings
from storage.database import db_manager, init_database
from storage.models import AnalysisRun
from data_ingestion.openalex_ingester import OpenAlexIngester
from data_ingestion.base_ingester import IngestionResult

logger = logging.getLogger(__name__)


class DataIngestionOrchestrator:
    """Orchestrates data ingestion from multiple sources."""
    
    def __init__(self):
        self.ingesters = {}
        self.analysis_run_id = None
        self._initialize_ingesters()
    
    def _initialize_ingesters(self):
        """Initialize all available data ingesters."""
        try:
            # Initialize OpenAlex ingester
            if settings.DATA_SOURCES["openalex"]["enabled"]:
                self.ingesters["openalex"] = OpenAlexIngester()
                logger.info("Initialized OpenAlex ingester")
            
            # Initialize other ingesters
            try:
                from data_ingestion.pubmed_ingester import PubMedIngester
                if settings.DATA_SOURCES["pubmed"]["enabled"]:
                    self.ingesters["pubmed"] = PubMedIngester()
                    logger.info("Initialized PubMed ingester")
            except ImportError:
                logger.warning("PubMed ingester not available")
                
            try:
                from data_ingestion.semantic_scholar_ingester import SemanticScholarIngester
                if settings.DATA_SOURCES["semantic_scholar"]["enabled"]:
                    self.ingesters["semantic_scholar"] = SemanticScholarIngester()
                    logger.info("Initialized Semantic Scholar ingester")
            except ImportError:
                logger.warning("Semantic Scholar ingester not available")
                
            try:
                from data_ingestion.world_bank_ingester import WorldBankIngester
                if settings.DATA_SOURCES["world_bank"]["enabled"]:
                    self.ingesters["world_bank"] = WorldBankIngester()
                    logger.info("Initialized World Bank ingester")
            except ImportError:
                logger.warning("World Bank ingester not available")
                
            try:
                from data_ingestion.nih_reporter_ingester import NIHReporterIngester
                if settings.DATA_SOURCES["nih_reporter"]["enabled"]:
                    self.ingesters["nih_reporter"] = NIHReporterIngester()
                    logger.info("Initialized NIH RePORTER ingester")
            except ImportError:
                logger.warning("NIH RePORTER ingester not available")
                
            try:
                from data_ingestion.cordis_ingester import CORDISIngester
                if settings.DATA_SOURCES["cordis"]["enabled"]:
                    self.ingesters["cordis"] = CORDISIngester()
                    logger.info("Initialized CORDIS ingester")
            except ImportError:
                logger.warning("CORDIS ingester not available")
                
            try:
                from data_ingestion.web_scraper_ingester import WebScraperIngester
                self.ingesters["web_scraper"] = WebScraperIngester()
                logger.info("Initialized Web Scraper ingester")
            except ImportError:
                logger.warning("Web Scraper ingester not available")
            
            logger.info(f"Initialized {len(self.ingesters)} data ingesters")
            
        except Exception as e:
            logger.error(f"Failed to initialize ingesters: {e}")
            raise
    
    def _create_analysis_run(self, run_name: str, run_type: str, 
                           parameters: Optional[Dict] = None) -> int:
        """Create a new analysis run record."""
        try:
            with db_manager.get_session() as session:
                analysis_run = AnalysisRun(
                    run_name=run_name,
                    run_type=run_type,
                    parameters=parameters,
                    data_sources_used=list(self.ingesters.keys()),
                    status="running",
                    start_time=datetime.now()
                )
                session.add(analysis_run)
                session.commit()
                session.refresh(analysis_run)
                return analysis_run.id
        except Exception as e:
            logger.error(f"Failed to create analysis run: {e}")
            raise
    
    def _update_analysis_run(self, run_id: int, status: str, 
                           items_processed: int = 0, items_successful: int = 0,
                           items_failed: int = 0, error_log: Optional[str] = None):
        """Update an analysis run record."""
        try:
            with db_manager.get_session() as session:
                analysis_run = session.query(AnalysisRun).filter(
                    AnalysisRun.id == run_id
                ).first()
                
                if analysis_run:
                    analysis_run.status = status
                    analysis_run.items_processed = items_processed
                    analysis_run.items_successful = items_successful
                    analysis_run.items_failed = items_failed
                    
                    if status == "completed":
                        analysis_run.end_time = datetime.now()
                        if analysis_run.start_time:
                            duration = (analysis_run.end_time - analysis_run.start_time).total_seconds()
                            analysis_run.duration_seconds = duration
                    
                    if error_log:
                        analysis_run.error_log = error_log
                    
                    session.commit()
                    logger.info(f"Updated analysis run {run_id}: {status}")
        except Exception as e:
            logger.error(f"Failed to update analysis run: {e}")
    
    async def run_full_ingestion(self, domains: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run a full data ingestion across all sources and domains."""
        if not domains:
            domains = list(settings.SEARCH_KEYWORDS.keys())
        
        run_name = f"full_ingestion_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.analysis_run_id = self._create_analysis_run(
            run_name=run_name,
            run_type="data_ingestion",
            parameters={"domains": domains}
        )
        
        logger.info(f"Starting full data ingestion (run ID: {self.analysis_run_id})")
        logger.info(f"Target domains: {domains}")
        
        total_results = {
            "run_id": self.analysis_run_id,
            "start_time": datetime.now(),
            "domains": domains,
            "sources": {},
            "summary": {
                "total_processed": 0,
                "total_successful": 0,
                "total_failed": 0,
                "errors": []
            }
        }
        
        try:
            # Process each domain
            for domain in domains:
                logger.info(f"Processing domain: {domain}")
                domain_keywords = settings.SEARCH_KEYWORDS.get(domain, [])
                
                if not domain_keywords:
                    logger.warning(f"No keywords found for domain: {domain}")
                    continue
                
                # Process each data source for this domain
                for source_name, ingester in self.ingesters.items():
                    logger.info(f"Processing {source_name} for domain {domain}")
                    
                    try:
                        async with ingester:
                            result = await ingester.ingest_domain_data(
                                domain=domain,
                                keywords=domain_keywords,
                                max_results_per_keyword=50
                            )
                            
                            # Store results
                            total_results["sources"][source_name] = {
                                "domain": domain,
                                "result": {
                                    "success": result.success,
                                    "items_processed": result.items_processed,
                                    "items_successful": result.items_successful,
                                    "items_failed": result.items_failed,
                                    "error_message": result.error_message,
                                    "metadata": result.metadata
                                }
                            }
                            
                            # Update summary
                            total_results["summary"]["total_processed"] += result.items_processed
                            total_results["summary"]["total_successful"] += result.items_successful
                            total_results["summary"]["total_failed"] += result.items_failed
                            
                            if result.error_message:
                                total_results["summary"]["errors"].append(
                                    f"{source_name}/{domain}: {result.error_message}"
                                )
                            
                            logger.info(f"Completed {source_name} for {domain}: "
                                       f"{result.items_successful} successful, {result.items_failed} failed")
                    
                    except Exception as e:
                        error_msg = f"Failed to process {source_name} for {domain}: {e}"
                        logger.error(error_msg)
                        total_results["summary"]["errors"].append(error_msg)
                        total_results["summary"]["total_failed"] += 1
                
                # Update analysis run progress
                self._update_analysis_run(
                    self.analysis_run_id,
                    "running",
                    total_results["summary"]["total_processed"],
                    total_results["summary"]["total_successful"],
                    total_results["summary"]["total_failed"]
                )
            
            # Mark analysis run as completed
            total_results["end_time"] = datetime.now()
            duration = (total_results["end_time"] - total_results["start_time"]).total_seconds()
            total_results["duration_seconds"] = duration
            
            self._update_analysis_run(
                self.analysis_run_id,
                "completed",
                total_results["summary"]["total_processed"],
                total_results["summary"]["total_successful"],
                total_results["summary"]["total_failed"]
            )
            
            logger.info(f"Full ingestion completed in {duration:.2f} seconds")
            logger.info(f"Summary: {total_results['summary']['total_successful']} successful, "
                       f"{total_results['summary']['total_failed']} failed")
            
            return total_results
            
        except Exception as e:
            error_msg = f"Full ingestion failed: {e}"
            logger.error(error_msg)
            total_results["summary"]["errors"].append(error_msg)
            
            self._update_analysis_run(
                self.analysis_run_id,
                "failed",
                total_results["summary"]["total_processed"],
                total_results["summary"]["total_successful"],
                total_results["summary"]["total_failed"],
                error_log=error_msg
            )
            
            return total_results
    
    async def run_source_ingestion(self, source_name: str, 
                                 domains: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run data ingestion for a specific source."""
        if source_name not in self.ingesters:
            raise ValueError(f"Unknown data source: {source_name}")
        
        if not domains:
            domains = list(settings.SEARCH_KEYWORDS.keys())
        
        run_name = f"{source_name}_ingestion_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.analysis_run_id = self._create_analysis_run(
            run_name=run_name,
            run_type="data_ingestion",
            parameters={"source": source_name, "domains": domains}
        )
        
        logger.info(f"Starting {source_name} ingestion (run ID: {self.analysis_run_id})")
        
        total_results = {
            "run_id": self.analysis_run_id,
            "source": source_name,
            "start_time": datetime.now(),
            "domains": domains,
            "results": {}
        }
        
        try:
            ingester = self.ingesters[source_name]
            
            async with ingester:
                for domain in domains:
                    logger.info(f"Processing {source_name} for domain: {domain}")
                    domain_keywords = settings.SEARCH_KEYWORDS.get(domain, [])
                    
                    if not domain_keywords:
                        logger.warning(f"No keywords found for domain: {domain}")
                        continue
                    
                    result = await ingester.ingest_domain_data(
                        domain=domain,
                        keywords=domain_keywords,
                        max_results_per_keyword=50
                    )
                    
                    total_results["results"][domain] = {
                        "success": result.success,
                        "items_processed": result.items_processed,
                        "items_successful": result.items_successful,
                        "items_failed": result.items_failed,
                        "error_message": result.error_message,
                        "metadata": result.metadata
                    }
            
            total_results["end_time"] = datetime.now()
            duration = (total_results["end_time"] - total_results["start_time"]).total_seconds()
            total_results["duration_seconds"] = duration
            
            # Calculate summary
            total_processed = sum(r["items_processed"] for r in total_results["results"].values())
            total_successful = sum(r["items_successful"] for r in total_results["results"].values())
            total_failed = sum(r["items_failed"] for r in total_results["results"].values())
            
            self._update_analysis_run(
                self.analysis_run_id,
                "completed",
                total_processed,
                total_successful,
                total_failed
            )
            
            logger.info(f"{source_name} ingestion completed in {duration:.2f} seconds")
            logger.info(f"Summary: {total_successful} successful, {total_failed} failed")
            
            return total_results
            
        except Exception as e:
            error_msg = f"{source_name} ingestion failed: {e}"
            logger.error(error_msg)
            
            self._update_analysis_run(
                self.analysis_run_id,
                "failed",
                0, 0, 1,
                error_log=error_msg
            )
            
            total_results["error"] = error_msg
            return total_results
    
    def get_ingestion_status(self, run_id: int) -> Optional[Dict[str, Any]]:
        """Get the status of a specific ingestion run."""
        try:
            with db_manager.get_session() as session:
                analysis_run = session.query(AnalysisRun).filter(
                    AnalysisRun.id == run_id
                ).first()
                
                if analysis_run:
                    return {
                        "run_id": analysis_run.id,
                        "run_name": analysis_run.run_name,
                        "run_type": analysis_run.run_type,
                        "status": analysis_run.status,
                        "start_time": analysis_run.start_time,
                        "end_time": analysis_run.end_time,
                        "duration_seconds": analysis_run.duration_seconds,
                        "items_processed": analysis_run.items_processed,
                        "items_successful": analysis_run.items_successful,
                        "items_failed": analysis_run.items_failed,
                        "error_log": analysis_run.error_log,
                        "parameters": analysis_run.parameters
                    }
                
                return None
        except Exception as e:
            logger.error(f"Failed to get ingestion status: {e}")
            return None


async def main():
    """Main function for running data ingestion."""
    # Initialize database
    init_database()
    
    # Create orchestrator
    orchestrator = DataIngestionOrchestrator()
    
    # Run full ingestion
    results = await orchestrator.run_full_ingestion()
    
    # Print results
    print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the main function
    asyncio.run(main())
