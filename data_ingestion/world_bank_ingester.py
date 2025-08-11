import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import quote_plus

from data_ingestion.base_ingester import BaseDataIngester, IngestionResult
from config.settings import settings

class WorldBankIngester(BaseDataIngester):
    def __init__(self):
        source_config = settings.DATA_SOURCES["world_bank"]
        super().__init__("world_bank", source_config)
        self.indicators_endpoint = source_config["indicators_endpoint"]
        self.projects_endpoint = source_config["projects_endpoint"]

    async def search(self, query: str, domain: Optional[str] = None, max_results: int = 100) -> IngestionResult:
        """Search World Bank data - this is a generic search that can be customized based on query type."""
        try:
            # Determine search type based on query
            if "indicator" in query.lower() or "data" in query.lower():
                return await self.search_indicators(query, domain, max_results)
            elif "project" in query.lower():
                return await self.search_projects(query, domain, max_results)
            else:
                # Default to indicators search
                return await self.search_indicators(query, domain, max_results)
                
        except Exception as e:
            logging.error(f"Error in World Bank search: {str(e)}")
            return IngestionResult(
                success=False,
                items_processed=0,
                items_successful=0,
                items_failed=1,
                error_message=str(e)
            )

    async def search_indicators(self, query: str, domain: Optional[str] = None, max_results: int = 100) -> IngestionResult:
        """Search World Bank development indicators."""
        try:
            # Parse query to extract indicator code or search terms
            indicator_code = None
            search_terms = query
            
            # Check if query contains an indicator code (e.g., SE.ADT.LITR.ZS)
            if "." in query and len(query.split(".")) >= 2:
                parts = query.split()
                for part in parts:
                    if "." in part and len(part.split(".")) >= 2:
                        indicator_code = part
                        search_terms = query.replace(part, "").strip()
                        break
            
            if indicator_code:
                return await self.get_indicator_data(indicator_code, domain, max_results)
            else:
                return await self.search_indicator_metadata(search_terms, domain, max_results)
                
        except Exception as e:
            logging.error(f"Error in World Bank indicators search: {str(e)}")
            return IngestionResult(
                success=False,
                items_processed=0,
                items_successful=0,
                items_failed=1,
                error_message=str(e)
            )

    async def get_indicator_data(self, indicator_code: str, domain: Optional[str] = None, max_results: int = 100) -> IngestionResult:
        """Get data for a specific World Bank indicator."""
        try:
            url = f"{self.base_url}{self.indicators_endpoint}/{indicator_code}"
            params = {
                "format": "json",
                "per_page": min(max_results, 100),
                "page": 1
            }
            
            response = await self._make_request(url, params)
            
            if not response:
                return IngestionResult(
                    success=False,
                    items_processed=0,
                    items_successful=0,
                    items_failed=1,
                    error_message="Failed to fetch indicator data"
                )

            # Process indicator data
            items_processed = 0
            items_successful = 0
            items_failed = 0
            
            # Extract indicator metadata
            indicator_info = response[0] if response else {}
            indicator_name = indicator_info.get("indicator", {}).get("value", "")
            indicator_source = indicator_info.get("indicator", {}).get("source", "")
            
            # Process data points
            data_points = response[1] if len(response) > 1 else []
            
            for data_point in data_points:
                items_processed += 1
                try:
                    country = data_point.get("country", {}).get("value", "")
                    value = data_point.get("value")
                    year = data_point.get("date", "")
                    
                    # Create content from data point
                    content = f"Indicator: {indicator_name}\nCountry: {country}\nValue: {value}\nYear: {year}"
                    
                    metadata = {
                        "indicator_code": indicator_code,
                        "indicator_name": indicator_name,
                        "indicator_source": indicator_source,
                        "country": country,
                        "value": value,
                        "year": year,
                        "data_type": "indicator"
                    }
                    
                    await self._save_raw_data(
                        content=content,
                        title=f"{indicator_name} - {country} ({year})",
                        source_id=f"{indicator_code}_{country}_{year}",
                        url=f"https://data.worldbank.org/indicator/{indicator_code}",
                        metadata=metadata,
                        domain=domain or "development"
                    )
                    items_successful += 1
                    
                except Exception as e:
                    logging.error(f"Failed to save indicator data point: {str(e)}")
                    items_failed += 1

            return IngestionResult(
                success=True,
                items_processed=items_processed,
                items_successful=items_successful,
                items_failed=items_failed,
                metadata={
                    "indicator_code": indicator_code,
                    "indicator_name": indicator_name,
                    "total_data_points": len(data_points)
                }
            )

        except Exception as e:
            logging.error(f"Error fetching indicator data: {str(e)}")
            return IngestionResult(
                success=False,
                items_processed=0,
                items_successful=0,
                items_failed=1,
                error_message=str(e)
            )

    async def search_indicator_metadata(self, search_terms: str, domain: Optional[str] = None, max_results: int = 100) -> IngestionResult:
        """Search for World Bank indicators by name/description."""
        try:
            # This would require a different endpoint or approach
            # For now, we'll use some common indicators
            common_indicators = [
                "SE.ADT.LITR.ZS",  # Literacy rate
                "NY.GDP.PCAP.CD",  # GDP per capita
                "SP.DYN.LE00.IN",  # Life expectancy
                "SE.PRM.ENRR",     # Primary school enrollment
                "SH.DYN.MORT",     # Under-5 mortality
                "EN.ATM.CO2E.PC",  # CO2 emissions per capita
                "SI.POV.DDAY",     # Poverty headcount ratio
                "SL.UEM.TOTL.ZS",  # Unemployment rate
                "SH.MED.BEDS.ZS",  # Hospital beds per 1000
                "SE.SEC.ENRR",     # Secondary school enrollment
            ]
            
            items_processed = 0
            items_successful = 0
            items_failed = 0
            
            for indicator_code in common_indicators[:max_results]:
                items_processed += 1
                try:
                    # Get indicator metadata
                    url = f"{self.base_url}/v2/indicator/{indicator_code}"
                    params = {"format": "json"}
                    
                    response = await self._make_request(url, params)
                    
                    if response and len(response) > 0:
                        indicator = response[0]
                        name = indicator.get("name", "")
                        source = indicator.get("source", {}).get("value", "")
                        topic = indicator.get("topics", [{}])[0].get("value", "") if indicator.get("topics") else ""
                        
                        content = f"Indicator: {name}\nSource: {source}\nTopic: {topic}\nCode: {indicator_code}"
                        
                        metadata = {
                            "indicator_code": indicator_code,
                            "indicator_name": name,
                            "indicator_source": source,
                            "topic": topic,
                            "data_type": "indicator_metadata"
                        }
                        
                        await self._save_raw_data(
                            content=content,
                            title=name,
                            source_id=indicator_code,
                            url=f"https://data.worldbank.org/indicator/{indicator_code}",
                            metadata=metadata,
                            domain=domain or "development"
                        )
                        items_successful += 1
                    else:
                        items_failed += 1
                        
                except Exception as e:
                    logging.error(f"Failed to fetch indicator metadata for {indicator_code}: {str(e)}")
                    items_failed += 1

            return IngestionResult(
                success=True,
                items_processed=items_processed,
                items_successful=items_successful,
                items_failed=items_failed,
                metadata={"search_terms": search_terms}
            )

        except Exception as e:
            logging.error(f"Error searching indicator metadata: {str(e)}")
            return IngestionResult(
                success=False,
                items_processed=0,
                items_successful=0,
                items_failed=1,
                error_message=str(e)
            )

    async def search_projects(self, query: str, domain: Optional[str] = None, max_results: int = 100) -> IngestionResult:
        """Search World Bank projects."""
        try:
            url = f"{self.base_url}{self.projects_endpoint}"
            params = {
                "format": "json",
                "per_page": min(max_results, 100),
                "page": 1
            }
            
            # Add search parameters if provided
            if query:
                params["search"] = query
            
            response = await self._make_request(url, params)
            
            if not response:
                return IngestionResult(
                    success=False,
                    items_processed=0,
                    items_successful=0,
                    items_failed=1,
                    error_message="Failed to fetch projects"
                )

            # Process projects
            items_processed = 0
            items_successful = 0
            items_failed = 0
            
            projects = response.get("projects", [])
            
            for project in projects:
                items_processed += 1
                try:
                    project_id = project.get("id", "")
                    project_name = project.get("name", "")
                    project_description = project.get("description", "")
                    project_status = project.get("status", "")
                    project_amount = project.get("totalamt", "")
                    project_country = project.get("countryname", "")
                    
                    content = f"Project: {project_name}\nDescription: {project_description}\nStatus: {project_status}\nAmount: {project_amount}\nCountry: {project_country}"
                    
                    metadata = {
                        "project_id": project_id,
                        "project_name": project_name,
                        "project_status": project_status,
                        "project_amount": project_amount,
                        "project_country": project_country,
                        "data_type": "project"
                    }
                    
                    await self._save_raw_data(
                        content=content,
                        title=project_name,
                        source_id=project_id,
                        url=f"https://projects.worldbank.org/en/projects-operations/project-detail/{project_id}",
                        metadata=metadata,
                        domain=domain or "development"
                    )
                    items_successful += 1
                    
                except Exception as e:
                    logging.error(f"Failed to save project: {str(e)}")
                    items_failed += 1

            return IngestionResult(
                success=True,
                items_processed=items_processed,
                items_successful=items_successful,
                items_failed=items_failed,
                metadata={
                    "query": query,
                    "total_projects": len(projects)
                }
            )

        except Exception as e:
            logging.error(f"Error searching projects: {str(e)}")
            return IngestionResult(
                success=False,
                items_processed=0,
                items_successful=0,
                items_failed=1,
                error_message=str(e)
            )

    async def get_country_data(self, country_code: str, indicators: List[str] = None, max_results: int = 100) -> IngestionResult:
        """Get data for a specific country across multiple indicators."""
        try:
            if not indicators:
                indicators = ["SE.ADT.LITR.ZS", "NY.GDP.PCAP.CD", "SP.DYN.LE00.IN"]
            
            items_processed = 0
            items_successful = 0
            items_failed = 0
            
            for indicator in indicators[:max_results]:
                items_processed += 1
                try:
                    result = await self.get_indicator_data(indicator, "development", 1)
                    if result.success:
                        items_successful += result.items_successful
                        items_failed += result.items_failed
                    else:
                        items_failed += 1
                except Exception as e:
                    logging.error(f"Failed to get indicator {indicator} for country {country_code}: {str(e)}")
                    items_failed += 1

            return IngestionResult(
                success=True,
                items_processed=items_processed,
                items_successful=items_successful,
                items_failed=items_failed,
                metadata={"country_code": country_code, "indicators": indicators}
            )

        except Exception as e:
            logging.error(f"Error getting country data: {str(e)}")
            return IngestionResult(
                success=False,
                items_processed=0,
                items_successful=0,
                items_failed=1,
                error_message=str(e)
            )

    async def get_region_data(self, region_code: str, indicators: List[str] = None, max_results: int = 100) -> IngestionResult:
        """Get data for a specific region across multiple indicators."""
        try:
            if not indicators:
                indicators = ["SE.ADT.LITR.ZS", "NY.GDP.PCAP.CD", "SP.DYN.LE00.IN"]
            
            items_processed = 0
            items_successful = 0
            items_failed = 0
            
            for indicator in indicators[:max_results]:
                items_processed += 1
                try:
                    # Modify URL to get regional data
                    url = f"{self.base_url}{self.indicators_endpoint}/{indicator}"
                    params = {
                        "format": "json",
                        "per_page": min(max_results, 100),
                        "page": 1,
                        "region": region_code
                    }
                    
                    response = await self._make_request(url, params)
                    
                    if response and len(response) > 1:
                        data_points = response[1]
                        for data_point in data_points:
                            try:
                                region = data_point.get("country", {}).get("value", "")
                                value = data_point.get("value")
                                year = data_point.get("date", "")
                                
                                content = f"Region: {region}\nIndicator: {indicator}\nValue: {value}\nYear: {year}"
                                
                                metadata = {
                                    "indicator_code": indicator,
                                    "region": region,
                                    "value": value,
                                    "year": year,
                                    "data_type": "regional_indicator"
                                }
                                
                                await self._save_raw_data(
                                    content=content,
                                    title=f"{indicator} - {region} ({year})",
                                    source_id=f"{indicator}_{region}_{year}",
                                    url=f"https://data.worldbank.org/indicator/{indicator}",
                                    metadata=metadata,
                                    domain="development"
                                )
                                items_successful += 1
                                
                            except Exception as e:
                                logging.error(f"Failed to save regional data point: {str(e)}")
                                items_failed += 1
                    else:
                        items_failed += 1
                        
                except Exception as e:
                    logging.error(f"Failed to get indicator {indicator} for region {region_code}: {str(e)}")
                    items_failed += 1

            return IngestionResult(
                success=True,
                items_processed=items_processed,
                items_successful=items_successful,
                items_failed=items_failed,
                metadata={"region_code": region_code, "indicators": indicators}
            )

        except Exception as e:
            logging.error(f"Error getting region data: {str(e)}")
            return IngestionResult(
                success=False,
                items_processed=0,
                items_successful=0,
                items_failed=1,
                error_message=str(e)
            )
