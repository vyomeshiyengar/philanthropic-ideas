import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import quote_plus

from data_ingestion.base_ingester import BaseDataIngester, IngestionResult
from config.settings import settings

class NIHReporterIngester(BaseDataIngester):
    def __init__(self):
        source_config = settings.DATA_SOURCES["nih_reporter"]
        super().__init__("nih_reporter", source_config)
        self.search_endpoint = source_config["search_endpoint"]
        self.api_key = settings.NIH_API_KEY

    async def search(self, query: str, domain: Optional[str] = None, max_results: int = 100) -> IngestionResult:
        """Search NIH RePORTER for funded projects matching the query."""
        try:
            # NIH RePORTER API parameters
            params = {
                "criteria": {
                    "text": query,
                    "include_active_projects": True,
                    "include_inactive_projects": True
                },
                "offset": 0,
                "limit": min(max_results, 500),  # NIH limit
                "fields": "ProjectNum,ProjectTitle,ProjectAbstract,PrincipalInvestigator,Organization,ProjectStartDate,ProjectEndDate,TotalCost,AgencyCode,StudySection,Keywords"
            }
            
            if self.api_key:
                params["api_key"] = self.api_key
            
            search_url = f"{self.base_url}{self.search_endpoint}"
            
            # NIH RePORTER expects POST requests with JSON body
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            if self.api_key:
                headers["api_key"] = self.api_key
            
            response = await self._make_request(search_url, params, method="POST", headers=headers)
            
            if not response:
                return IngestionResult(
                    success=False,
                    items_processed=0,
                    items_successful=0,
                    items_failed=1,
                    error_message="Failed to search NIH RePORTER"
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
                    project_num = project.get("ProjectNum", "")
                    project_title = project.get("ProjectTitle", "")
                    project_abstract = project.get("ProjectAbstract", "")
                    principal_investigator = project.get("PrincipalInvestigator", "")
                    organization = project.get("Organization", "")
                    project_start = project.get("ProjectStartDate", "")
                    project_end = project.get("ProjectEndDate", "")
                    total_cost = project.get("TotalCost", "")
                    agency_code = project.get("AgencyCode", "")
                    study_section = project.get("StudySection", "")
                    keywords = project.get("Keywords", [])
                    
                    # Create content from project
                    content = f"Project: {project_title}\nAbstract: {project_abstract}\nPrincipal Investigator: {principal_investigator}\nOrganization: {organization}\nStart Date: {project_start}\nEnd Date: {project_end}\nTotal Cost: {total_cost}\nAgency: {agency_code}\nStudy Section: {study_section}"
                    
                    if keywords:
                        content += f"\nKeywords: {', '.join(keywords)}"
                    
                    metadata = {
                        "project_num": project_num,
                        "principal_investigator": principal_investigator,
                        "organization": organization,
                        "project_start_date": project_start,
                        "project_end_date": project_end,
                        "total_cost": total_cost,
                        "agency_code": agency_code,
                        "study_section": study_section,
                        "keywords": keywords,
                        "data_type": "nih_project"
                    }
                    
                    # Save to database
                    await self._save_raw_data(
                        content_type="nih_project",
                        title=project_title,
                        full_text=content,
                        url=f"https://reporter.nih.gov/project-details/{project_num}",
                        metadata=metadata
                    )
                    items_successful += 1
                    
                except Exception as e:
                    logging.error(f"Failed to save project {project.get('ProjectNum', 'unknown')}: {str(e)}")
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
            logging.error(f"Error in NIH RePORTER search: {str(e)}")
            return IngestionResult(
                success=False,
                items_processed=0,
                items_successful=0,
                items_failed=1,
                error_message=str(e)
            )

    async def search_by_investigator(self, investigator_name: str, max_results: int = 100) -> IngestionResult:
        """Search for projects by principal investigator name."""
        try:
            params = {
                "criteria": {
                    "pi_names": [investigator_name],
                    "include_active_projects": True,
                    "include_inactive_projects": True
                },
                "offset": 0,
                "limit": min(max_results, 500),
                "fields": "ProjectNum,ProjectTitle,ProjectAbstract,PrincipalInvestigator,Organization,ProjectStartDate,ProjectEndDate,TotalCost,AgencyCode,StudySection,Keywords"
            }
            
            if self.api_key:
                params["api_key"] = self.api_key
            
            search_url = f"{self.base_url}{self.search_endpoint}"
            headers = {"Content-Type": "application/json"}
            
            if self.api_key:
                headers["api_key"] = self.api_key
            
            response = await self._make_request(search_url, params, method="POST", headers=headers)
            
            if not response:
                return IngestionResult(
                    success=False,
                    items_processed=0,
                    items_successful=0,
                    items_failed=1,
                    error_message="Failed to search by investigator"
                )

            # Process results similar to main search
            items_processed = 0
            items_successful = 0
            items_failed = 0
            
            projects = response.get("results", [])
            
            for project in projects:
                items_processed += 1
                try:
                    project_num = project.get("ProjectNum", "")
                    project_title = project.get("ProjectTitle", "")
                    project_abstract = project.get("ProjectAbstract", "")
                    principal_investigator = project.get("PrincipalInvestigator", "")
                    organization = project.get("Organization", "")
                    
                    content = f"Project: {project_title}\nAbstract: {project_abstract}\nPrincipal Investigator: {principal_investigator}\nOrganization: {organization}"
                    
                    metadata = {
                        "project_num": project_num,
                        "principal_investigator": principal_investigator,
                        "organization": organization,
                        "data_type": "nih_project_by_investigator"
                    }
                    
                    await self._save_raw_data(
                        content_type="nih_project_by_investigator",
                        title=project_title,
                        full_text=content,
                        url=f"https://reporter.nih.gov/project-details/{project_num}",
                        metadata=metadata
                    )
                    items_successful += 1
                    
                except Exception as e:
                    logging.error(f"Failed to save project {project.get('ProjectNum', 'unknown')}: {str(e)}")
                    items_failed += 1

            return IngestionResult(
                success=True,
                items_processed=items_processed,
                items_successful=items_successful,
                items_failed=items_failed,
                metadata={"investigator": investigator_name}
            )

        except Exception as e:
            logging.error(f"Error searching by investigator: {str(e)}")
            return IngestionResult(
                success=False,
                items_processed=0,
                items_successful=0,
                items_failed=1,
                error_message=str(e)
            )

    async def search_by_organization(self, organization_name: str, max_results: int = 100) -> IngestionResult:
        """Search for projects by organization/institution."""
        try:
            params = {
                "criteria": {
                    "org_names": [organization_name],
                    "include_active_projects": True,
                    "include_inactive_projects": True
                },
                "offset": 0,
                "limit": min(max_results, 500),
                "fields": "ProjectNum,ProjectTitle,ProjectAbstract,PrincipalInvestigator,Organization,ProjectStartDate,ProjectEndDate,TotalCost,AgencyCode,StudySection,Keywords"
            }
            
            if self.api_key:
                params["api_key"] = self.api_key
            
            search_url = f"{self.base_url}{self.search_endpoint}"
            headers = {"Content-Type": "application/json"}
            
            if self.api_key:
                headers["api_key"] = self.api_key
            
            response = await self._make_request(search_url, params, method="POST", headers=headers)
            
            if not response:
                return IngestionResult(
                    success=False,
                    items_processed=0,
                    items_successful=0,
                    items_failed=1,
                    error_message="Failed to search by organization"
                )

            # Process results
            items_processed = 0
            items_successful = 0
            items_failed = 0
            
            projects = response.get("results", [])
            
            for project in projects:
                items_processed += 1
                try:
                    project_num = project.get("ProjectNum", "")
                    project_title = project.get("ProjectTitle", "")
                    project_abstract = project.get("ProjectAbstract", "")
                    principal_investigator = project.get("PrincipalInvestigator", "")
                    organization = project.get("Organization", "")
                    
                    content = f"Project: {project_title}\nAbstract: {project_abstract}\nPrincipal Investigator: {principal_investigator}\nOrganization: {organization}"
                    
                    metadata = {
                        "project_num": project_num,
                        "principal_investigator": principal_investigator,
                        "organization": organization,
                        "data_type": "nih_project_by_organization"
                    }
                    
                    await self._save_raw_data(
                        content_type="nih_project_by_organization",
                        title=project_title,
                        full_text=content,
                        url=f"https://reporter.nih.gov/project-details/{project_num}",
                        metadata=metadata
                    )
                    items_successful += 1
                    
                except Exception as e:
                    logging.error(f"Failed to save project {project.get('ProjectNum', 'unknown')}: {str(e)}")
                    items_failed += 1

            return IngestionResult(
                success=True,
                items_processed=items_processed,
                items_successful=items_successful,
                items_failed=items_failed,
                metadata={"organization": organization_name}
            )

        except Exception as e:
            logging.error(f"Error searching by organization: {str(e)}")
            return IngestionResult(
                success=False,
                items_processed=0,
                items_successful=0,
                items_failed=1,
                error_message=str(e)
            )

    async def search_by_funding_amount(self, min_amount: float = 0, max_amount: float = None, max_results: int = 100) -> IngestionResult:
        """Search for projects within a specific funding amount range."""
        try:
            criteria = {
                "include_active_projects": True,
                "include_inactive_projects": True
            }
            
            if min_amount > 0:
                criteria["total_cost_min"] = min_amount
            
            if max_amount:
                criteria["total_cost_max"] = max_amount
            
            params = {
                "criteria": criteria,
                "offset": 0,
                "limit": min(max_results, 500),
                "fields": "ProjectNum,ProjectTitle,ProjectAbstract,PrincipalInvestigator,Organization,ProjectStartDate,ProjectEndDate,TotalCost,AgencyCode,StudySection,Keywords"
            }
            
            if self.api_key:
                params["api_key"] = self.api_key
            
            search_url = f"{self.base_url}{self.search_endpoint}"
            headers = {"Content-Type": "application/json"}
            
            if self.api_key:
                headers["api_key"] = self.api_key
            
            response = await self._make_request(search_url, params, method="POST", headers=headers)
            
            if not response:
                return IngestionResult(
                    success=False,
                    items_processed=0,
                    items_successful=0,
                    items_failed=1,
                    error_message="Failed to search by funding amount"
                )

            # Process results
            items_processed = 0
            items_successful = 0
            items_failed = 0
            
            projects = response.get("results", [])
            
            for project in projects:
                items_processed += 1
                try:
                    project_num = project.get("ProjectNum", "")
                    project_title = project.get("ProjectTitle", "")
                    project_abstract = project.get("ProjectAbstract", "")
                    total_cost = project.get("TotalCost", "")
                    
                    content = f"Project: {project_title}\nAbstract: {project_abstract}\nTotal Cost: {total_cost}"
                    
                    metadata = {
                        "project_num": project_num,
                        "total_cost": total_cost,
                        "data_type": "nih_project_by_funding"
                    }
                    
                    await self._save_raw_data(
                        content_type="nih_project_by_funding",
                        title=project_title,
                        full_text=content,
                        url=f"https://reporter.nih.gov/project-details/{project_num}",
                        metadata=metadata
                    )
                    items_successful += 1
                    
                except Exception as e:
                    logging.error(f"Failed to save project {project.get('ProjectNum', 'unknown')}: {str(e)}")
                    items_failed += 1

            return IngestionResult(
                success=True,
                items_processed=items_processed,
                items_successful=items_successful,
                items_failed=items_failed,
                metadata={"min_amount": min_amount, "max_amount": max_amount}
            )

        except Exception as e:
            logging.error(f"Error searching by funding amount: {str(e)}")
            return IngestionResult(
                success=False,
                items_processed=0,
                items_successful=0,
                items_failed=1,
                error_message=str(e)
            )

    async def search_recent_projects(self, days: int = 365, max_results: int = 100) -> IngestionResult:
        """Search for recently funded projects."""
        try:
            from datetime import datetime, timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            params = {
                "criteria": {
                    "project_start_date_from": start_date.strftime("%m/%d/%Y"),
                    "project_start_date_to": end_date.strftime("%m/%d/%Y"),
                    "include_active_projects": True,
                    "include_inactive_projects": True
                },
                "offset": 0,
                "limit": min(max_results, 500),
                "fields": "ProjectNum,ProjectTitle,ProjectAbstract,PrincipalInvestigator,Organization,ProjectStartDate,ProjectEndDate,TotalCost,AgencyCode,StudySection,Keywords"
            }
            
            if self.api_key:
                params["api_key"] = self.api_key
            
            search_url = f"{self.base_url}{self.search_endpoint}"
            headers = {"Content-Type": "application/json"}
            
            if self.api_key:
                headers["api_key"] = self.api_key
            
            response = await self._make_request(search_url, params, method="POST", headers=headers)
            
            if not response:
                return IngestionResult(
                    success=False,
                    items_processed=0,
                    items_successful=0,
                    items_failed=1,
                    error_message="Failed to search recent projects"
                )

            # Process results
            items_processed = 0
            items_successful = 0
            items_failed = 0
            
            projects = response.get("results", [])
            
            for project in projects:
                items_processed += 1
                try:
                    project_num = project.get("ProjectNum", "")
                    project_title = project.get("ProjectTitle", "")
                    project_abstract = project.get("ProjectAbstract", "")
                    project_start = project.get("ProjectStartDate", "")
                    
                    content = f"Project: {project_title}\nAbstract: {project_abstract}\nStart Date: {project_start}"
                    
                    metadata = {
                        "project_num": project_num,
                        "project_start_date": project_start,
                        "data_type": "nih_recent_project"
                    }
                    
                    await self._save_raw_data(
                        content_type="nih_recent_project",
                        title=project_title,
                        full_text=content,
                        url=f"https://reporter.nih.gov/project-details/{project_num}",
                        metadata=metadata
                    )
                    items_successful += 1
                    
                except Exception as e:
                    logging.error(f"Failed to save project {project.get('ProjectNum', 'unknown')}: {str(e)}")
                    items_failed += 1

            return IngestionResult(
                success=True,
                items_processed=items_processed,
                items_successful=items_successful,
                items_failed=items_failed,
                metadata={"days_back": days}
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

    async def fetch_details(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed information for a specific NIH project."""
        try:
            # NIH RePORTER doesn't have a direct details endpoint
            # We'll construct the URL and try to get basic info
            project_url = f"https://reporter.nih.gov/project-details/{item_id}"
            
            # For now, return basic project info
            # In a full implementation, you might scrape the project page
            return {
                "project_id": item_id,
                "url": project_url,
                "source": "nih_reporter",
                "note": "Detailed project information available at the URL"
            }
            
        except Exception as e:
            logging.error(f"Error fetching details for project {item_id}: {str(e)}")
            return None
