import logging
import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import quote_plus

from data_ingestion.base_ingester import BaseDataIngester, IngestionResult
from config.settings import settings

class CORDISIngester(BaseDataIngester):
    def __init__(self):
        source_config = settings.DATA_SOURCES["cordis"]
        super().__init__("cordis", source_config)
        self.projects_endpoint = source_config["projects_endpoint"]

    async def search(self, query: str, domain: Optional[str] = None, max_results: int = 100) -> IngestionResult:
        """Search CORDIS for EU-funded projects matching the query."""
        try:
            # CORDIS API parameters
            params = {
                "q": query,
                "num": min(max_results, 100),  # CORDIS limit
                "start": 0,
                "format": "json"
            }
            
            search_url = f"{self.base_url}{self.projects_endpoint}"
            response = await self._make_request(search_url, params)
            
            if not response:
                return IngestionResult(
                    success=False,
                    items_processed=0,
                    items_successful=0,
                    items_failed=1,
                    error_message="Failed to search CORDIS"
                )

            # Process results
            items_processed = 0
            items_successful = 0
            items_failed = 0
            
            projects = response.get("results", [])
            total = response.get("total", 0)
            
            for project in projects:
                items_processed += 1
                try:
                    # Extract project details
                    project_id = project.get("id", "")
                    project_title = project.get("title", "")
                    project_description = project.get("description", "")
                    project_objective = project.get("objective", "")
                    project_start_date = project.get("startDate", "")
                    project_end_date = project.get("endDate", "")
                    project_budget = project.get("totalCost", "")
                    project_coordinator = project.get("coordinator", "")
                    project_partners = project.get("participants", [])
                    project_topics = project.get("topics", [])
                    project_programme = project.get("programme", "")
                    
                    # Create content from project
                    content = f"Project: {project_title}\nDescription: {project_description}\nObjective: {project_objective}\nCoordinator: {project_coordinator}\nStart Date: {project_start_date}\nEnd Date: {project_end_date}\nBudget: {project_budget}\nProgramme: {project_programme}"
                    
                    if project_partners:
                        content += f"\nPartners: {', '.join(project_partners)}"
                    
                    if project_topics:
                        content += f"\nTopics: {', '.join(project_topics)}"
                    
                    metadata = {
                        "project_id": project_id,
                        "project_title": project_title,
                        "project_coordinator": project_coordinator,
                        "project_start_date": project_start_date,
                        "project_end_date": project_end_date,
                        "project_budget": project_budget,
                        "project_partners": project_partners,
                        "project_topics": project_topics,
                        "project_programme": project_programme,
                        "data_type": "cordis_project"
                    }
                    
                    # Save to database
                    await self._save_raw_data(
                        content=content,
                        title=project_title,
                        source_id=project_id,
                        url=f"https://cordis.europa.eu/project/id/{project_id}",
                        metadata=metadata,
                        domain=domain or "eu_research"
                    )
                    items_successful += 1
                    
                except Exception as e:
                    logging.error(f"Failed to save project {project.get('id', 'unknown')}: {str(e)}")
                    items_failed += 1

            return IngestionResult(
                success=True,
                items_processed=items_processed,
                items_successful=items_successful,
                items_failed=items_failed,
                metadata={
                    "total_results": total,
                    "query": query
                }
            )

        except Exception as e:
            logging.error(f"Error in CORDIS search: {str(e)}")
            return IngestionResult(
                success=False,
                items_processed=0,
                items_successful=0,
                items_failed=1,
                error_message=str(e)
            )

    async def search_by_programme(self, programme: str, max_results: int = 100) -> IngestionResult:
        """Search for projects by EU programme (e.g., FP7, H2020, Horizon Europe)."""
        try:
            params = {
                "q": f"programme:{programme}",
                "num": min(max_results, 100),
                "start": 0,
                "format": "json"
            }
            
            search_url = f"{self.base_url}{self.projects_endpoint}"
            response = await self._make_request(search_url, params)
            
            if not response:
                return IngestionResult(
                    success=False,
                    items_processed=0,
                    items_successful=0,
                    items_failed=1,
                    error_message="Failed to search by programme"
                )

            # Process results
            items_processed = 0
            items_successful = 0
            items_failed = 0
            
            projects = response.get("results", [])
            
            for project in projects:
                items_processed += 1
                try:
                    project_id = project.get("id", "")
                    project_title = project.get("title", "")
                    project_description = project.get("description", "")
                    project_programme = project.get("programme", "")
                    
                    content = f"Project: {project_title}\nDescription: {project_description}\nProgramme: {project_programme}"
                    
                    metadata = {
                        "project_id": project_id,
                        "project_programme": project_programme,
                        "data_type": "cordis_project_by_programme"
                    }
                    
                    await self._save_raw_data(
                        content=content,
                        title=project_title,
                        source_id=project_id,
                        url=f"https://cordis.europa.eu/project/id/{project_id}",
                        metadata=metadata,
                        domain="eu_research"
                    )
                    items_successful += 1
                    
                except Exception as e:
                    logging.error(f"Failed to save project {project.get('id', 'unknown')}: {str(e)}")
                    items_failed += 1

            return IngestionResult(
                success=True,
                items_processed=items_processed,
                items_successful=items_successful,
                items_failed=items_failed,
                metadata={"programme": programme}
            )

        except Exception as e:
            logging.error(f"Error searching by programme: {str(e)}")
            return IngestionResult(
                success=False,
                items_processed=0,
                items_successful=0,
                items_failed=1,
                error_message=str(e)
            )

    async def search_by_topic(self, topic: str, max_results: int = 100) -> IngestionResult:
        """Search for projects by research topic."""
        try:
            params = {
                "q": f"topic:{topic}",
                "num": min(max_results, 100),
                "start": 0,
                "format": "json"
            }
            
            search_url = f"{self.base_url}{self.projects_endpoint}"
            response = await self._make_request(search_url, params)
            
            if not response:
                return IngestionResult(
                    success=False,
                    items_processed=0,
                    items_successful=0,
                    items_failed=1,
                    error_message="Failed to search by topic"
                )

            # Process results
            items_processed = 0
            items_successful = 0
            items_failed = 0
            
            projects = response.get("results", [])
            
            for project in projects:
                items_processed += 1
                try:
                    project_id = project.get("id", "")
                    project_title = project.get("title", "")
                    project_description = project.get("description", "")
                    project_topics = project.get("topics", [])
                    
                    content = f"Project: {project_title}\nDescription: {project_description}\nTopics: {', '.join(project_topics)}"
                    
                    metadata = {
                        "project_id": project_id,
                        "project_topics": project_topics,
                        "data_type": "cordis_project_by_topic"
                    }
                    
                    await self._save_raw_data(
                        content=content,
                        title=project_title,
                        source_id=project_id,
                        url=f"https://cordis.europa.eu/project/id/{project_id}",
                        metadata=metadata,
                        domain="eu_research"
                    )
                    items_successful += 1
                    
                except Exception as e:
                    logging.error(f"Failed to save project {project.get('id', 'unknown')}: {str(e)}")
                    items_failed += 1

            return IngestionResult(
                success=True,
                items_processed=items_processed,
                items_successful=items_successful,
                items_failed=items_failed,
                metadata={"topic": topic}
            )

        except Exception as e:
            logging.error(f"Error searching by topic: {str(e)}")
            return IngestionResult(
                success=False,
                items_processed=0,
                items_successful=0,
                items_failed=1,
                error_message=str(e)
            )

    async def search_by_coordinator(self, coordinator: str, max_results: int = 100) -> IngestionResult:
        """Search for projects by coordinator organization."""
        try:
            params = {
                "q": f"coordinator:{coordinator}",
                "num": min(max_results, 100),
                "start": 0,
                "format": "json"
            }
            
            search_url = f"{self.base_url}{self.projects_endpoint}"
            response = await self._make_request(search_url, params)
            
            if not response:
                return IngestionResult(
                    success=False,
                    items_processed=0,
                    items_successful=0,
                    items_failed=1,
                    error_message="Failed to search by coordinator"
                )

            # Process results
            items_processed = 0
            items_successful = 0
            items_failed = 0
            
            projects = response.get("results", [])
            
            for project in projects:
                items_processed += 1
                try:
                    project_id = project.get("id", "")
                    project_title = project.get("title", "")
                    project_description = project.get("description", "")
                    project_coordinator = project.get("coordinator", "")
                    
                    content = f"Project: {project_title}\nDescription: {project_description}\nCoordinator: {project_coordinator}"
                    
                    metadata = {
                        "project_id": project_id,
                        "project_coordinator": project_coordinator,
                        "data_type": "cordis_project_by_coordinator"
                    }
                    
                    await self._save_raw_data(
                        content=content,
                        title=project_title,
                        source_id=project_id,
                        url=f"https://cordis.europa.eu/project/id/{project_id}",
                        metadata=metadata,
                        domain="eu_research"
                    )
                    items_successful += 1
                    
                except Exception as e:
                    logging.error(f"Failed to save project {project.get('id', 'unknown')}: {str(e)}")
                    items_failed += 1

            return IngestionResult(
                success=True,
                items_processed=items_processed,
                items_successful=items_successful,
                items_failed=items_failed,
                metadata={"coordinator": coordinator}
            )

        except Exception as e:
            logging.error(f"Error searching by coordinator: {str(e)}")
            return IngestionResult(
                success=False,
                items_processed=0,
                items_successful=0,
                items_failed=1,
                error_message=str(e)
            )

    async def search_by_date_range(self, start_date: str, end_date: str, max_results: int = 100) -> IngestionResult:
        """Search for projects within a specific date range."""
        try:
            params = {
                "q": f"startDate:[{start_date} TO {end_date}]",
                "num": min(max_results, 100),
                "start": 0,
                "format": "json"
            }
            
            search_url = f"{self.base_url}{self.projects_endpoint}"
            response = await self._make_request(search_url, params)
            
            if not response:
                return IngestionResult(
                    success=False,
                    items_processed=0,
                    items_successful=0,
                    items_failed=1,
                    error_message="Failed to search by date range"
                )

            # Process results
            items_processed = 0
            items_successful = 0
            items_failed = 0
            
            projects = response.get("results", [])
            
            for project in projects:
                items_processed += 1
                try:
                    project_id = project.get("id", "")
                    project_title = project.get("title", "")
                    project_description = project.get("description", "")
                    project_start_date = project.get("startDate", "")
                    project_end_date = project.get("endDate", "")
                    
                    content = f"Project: {project_title}\nDescription: {project_description}\nStart Date: {project_start_date}\nEnd Date: {project_end_date}"
                    
                    metadata = {
                        "project_id": project_id,
                        "project_start_date": project_start_date,
                        "project_end_date": project_end_date,
                        "data_type": "cordis_project_by_date"
                    }
                    
                    await self._save_raw_data(
                        content=content,
                        title=project_title,
                        source_id=project_id,
                        url=f"https://cordis.europa.eu/project/id/{project_id}",
                        metadata=metadata,
                        domain="eu_research"
                    )
                    items_successful += 1
                    
                except Exception as e:
                    logging.error(f"Failed to save project {project.get('id', 'unknown')}: {str(e)}")
                    items_failed += 1

            return IngestionResult(
                success=True,
                items_processed=items_processed,
                items_successful=items_successful,
                items_failed=items_failed,
                metadata={"start_date": start_date, "end_date": end_date}
            )

        except Exception as e:
            logging.error(f"Error searching by date range: {str(e)}")
            return IngestionResult(
                success=False,
                items_processed=0,
                items_successful=0,
                items_failed=1,
                error_message=str(e)
            )

    async def get_project_details(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific project."""
        try:
            url = f"{self.base_url}/project/{project_id}"
            params = {"format": "json"}
            
            response = await self._make_request(url, params)
            return response
            
        except Exception as e:
            logging.error(f"Error fetching project details {project_id}: {str(e)}")
            return None

    async def search_recent_projects(self, days: int = 365, max_results: int = 100) -> IngestionResult:
        """Search for recently started projects."""
        try:
            from datetime import datetime, timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            return await self.search_by_date_range(
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
                max_results
            )

        except Exception as e:
            logging.error(f"Error searching recent projects: {str(e)}")
            return IngestionResult(
                success=False,
                items_processed=0,
                items_successful=0,
                items_failed=1,
                error_message=str(e)
            )
