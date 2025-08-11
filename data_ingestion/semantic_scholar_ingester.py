import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import quote_plus

from data_ingestion.base_ingester import BaseDataIngester, IngestionResult
from config.settings import settings

class SemanticScholarIngester(BaseDataIngester):
    def __init__(self):
        source_config = settings.DATA_SOURCES["semantic_scholar"]
        super().__init__("semantic_scholar", source_config)
        self.search_endpoint = source_config["search_endpoint"]
        self.api_key = settings.SEMANTIC_SCHOLAR_API_KEY

    async def search(self, query: str, domain: Optional[str] = None, max_results: int = 100) -> IngestionResult:
        """Search Semantic Scholar for papers matching the query."""
        try:
            # Semantic Scholar API parameters
            params = {
                "query": query,
                "limit": min(max_results, 100),  # API limit
                "offset": 0,
                "fields": "paperId,title,abstract,authors,year,venue,url,referenceCount,citationCount,influentialCitationCount,fieldsOfStudy,publicationTypes,publicationDate"
            }
            
            if self.api_key:
                params["api_key"] = self.api_key
            
            search_url = f"{self.base_url}{self.search_endpoint}"
            response = await self._make_request(search_url, params)
            
            if not response:
                return IngestionResult(
                    success=False,
                    items_processed=0,
                    items_successful=0,
                    items_failed=1,
                    error_message="Failed to search Semantic Scholar"
                )

            # Process results
            items_processed = 0
            items_successful = 0
            items_failed = 0
            
            papers = response.get("data", [])
            total = response.get("total", 0)
            
            for paper in papers:
                items_processed += 1
                try:
                    # Extract paper details
                    paper_id = paper.get("paperId", "")
                    title = paper.get("title", "")
                    abstract = paper.get("abstract", "")
                    
                    # Extract authors
                    authors = []
                    for author in paper.get("authors", []):
                        if "name" in author:
                            authors.append(author["name"])
                    
                    # Extract fields of study
                    fields_of_study = paper.get("fieldsOfStudy", [])
                    
                    # Create metadata
                    metadata = {
                        "authors": authors,
                        "year": paper.get("year"),
                        "venue": paper.get("venue"),
                        "reference_count": paper.get("referenceCount"),
                        "citation_count": paper.get("citationCount"),
                        "influential_citation_count": paper.get("influentialCitationCount"),
                        "fields_of_study": fields_of_study,
                        "publication_types": paper.get("publicationTypes", []),
                        "publication_date": paper.get("publicationDate")
                    }
                    
                    # Save to database
                    await self._save_raw_data(
                        content=abstract,
                        title=title,
                        source_id=paper_id,
                        url=paper.get("url", f"https://www.semanticscholar.org/paper/{paper_id}"),
                        metadata=metadata,
                        domain=domain
                    )
                    items_successful += 1
                    
                except Exception as e:
                    logging.error(f"Failed to save paper {paper.get('paperId', 'unknown')}: {str(e)}")
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
            logging.error(f"Error in Semantic Scholar search: {str(e)}")
            return IngestionResult(
                success=False,
                items_processed=0,
                items_successful=0,
                items_failed=1,
                error_message=str(e)
            )

    async def search_by_paper_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed information for a specific paper by ID."""
        try:
            url = f"{self.base_url}/graph/v1/paper/{paper_id}"
            params = {
                "fields": "paperId,title,abstract,authors,year,venue,url,referenceCount,citationCount,influentialCitationCount,fieldsOfStudy,publicationTypes,publicationDate,references,citations"
            }
            
            if self.api_key:
                params["api_key"] = self.api_key
            
            response = await self._make_request(url, params)
            return response
            
        except Exception as e:
            logging.error(f"Error fetching paper {paper_id}: {str(e)}")
            return None

    async def search_by_author(self, author_name: str, max_results: int = 100) -> IngestionResult:
        """Search for papers by a specific author."""
        query = f'author:"{author_name}"'
        return await self.search(query, max_results=max_results)

    async def search_by_venue(self, venue_name: str, max_results: int = 100) -> IngestionResult:
        """Search for papers from a specific venue/journal."""
        query = f'venue:"{venue_name}"'
        return await self.search(query, max_results=max_results)

    async def search_by_year_range(self, start_year: int, end_year: int, query: str = "", max_results: int = 100) -> IngestionResult:
        """Search for papers within a specific year range."""
        year_filter = f"year:{start_year}-{end_year}"
        if query:
            full_query = f"{query} {year_filter}"
        else:
            full_query = year_filter
        return await self.search(full_query, max_results=max_results)

    async def get_paper_references(self, paper_id: str, max_results: int = 100) -> IngestionResult:
        """Get references for a specific paper."""
        try:
            url = f"{self.base_url}/graph/v1/paper/{paper_id}/references"
            params = {
                "limit": min(max_results, 100),
                "fields": "paperId,title,abstract,authors,year,venue,url"
            }
            
            if self.api_key:
                params["api_key"] = self.api_key
            
            response = await self._make_request(url, params)
            
            if not response:
                return IngestionResult(
                    success=False,
                    items_processed=0,
                    items_successful=0,
                    items_failed=1,
                    error_message="Failed to fetch references"
                )

            # Process references
            items_processed = 0
            items_successful = 0
            items_failed = 0
            
            references = response.get("data", [])
            
            for ref in references:
                items_processed += 1
                try:
                    cited_paper = ref.get("citedPaper", {})
                    
                    # Extract authors
                    authors = []
                    for author in cited_paper.get("authors", []):
                        if "name" in author:
                            authors.append(author["name"])
                    
                    metadata = {
                        "authors": authors,
                        "year": cited_paper.get("year"),
                        "venue": cited_paper.get("venue"),
                        "reference_type": "citation"
                    }
                    
                    await self._save_raw_data(
                        content=cited_paper.get("abstract", ""),
                        title=cited_paper.get("title", ""),
                        source_id=cited_paper.get("paperId", ""),
                        url=cited_paper.get("url", ""),
                        metadata=metadata,
                        domain="academic"
                    )
                    items_successful += 1
                    
                except Exception as e:
                    logging.error(f"Failed to save reference: {str(e)}")
                    items_failed += 1

            return IngestionResult(
                success=True,
                items_processed=items_processed,
                items_successful=items_successful,
                items_failed=items_failed,
                metadata={"paper_id": paper_id}
            )

        except Exception as e:
            logging.error(f"Error fetching references for {paper_id}: {str(e)}")
            return IngestionResult(
                success=False,
                items_processed=0,
                items_successful=0,
                items_failed=1,
                error_message=str(e)
            )

    async def get_paper_citations(self, paper_id: str, max_results: int = 100) -> IngestionResult:
        """Get papers that cite a specific paper."""
        try:
            url = f"{self.base_url}/graph/v1/paper/{paper_id}/citations"
            params = {
                "limit": min(max_results, 100),
                "fields": "paperId,title,abstract,authors,year,venue,url"
            }
            
            if self.api_key:
                params["api_key"] = self.api_key
            
            response = await self._make_request(url, params)
            
            if not response:
                return IngestionResult(
                    success=False,
                    items_processed=0,
                    items_successful=0,
                    items_failed=1,
                    error_message="Failed to fetch citations"
                )

            # Process citations
            items_processed = 0
            items_successful = 0
            items_failed = 0
            
            citations = response.get("data", [])
            
            for citation in citations:
                items_processed += 1
                try:
                    citing_paper = citation.get("citingPaper", {})
                    
                    # Extract authors
                    authors = []
                    for author in citing_paper.get("authors", []):
                        if "name" in author:
                            authors.append(author["name"])
                    
                    metadata = {
                        "authors": authors,
                        "year": citing_paper.get("year"),
                        "venue": citing_paper.get("venue"),
                        "reference_type": "citation"
                    }
                    
                    await self._save_raw_data(
                        content=citing_paper.get("abstract", ""),
                        title=citing_paper.get("title", ""),
                        source_id=citing_paper.get("paperId", ""),
                        url=citing_paper.get("url", ""),
                        metadata=metadata,
                        domain="academic"
                    )
                    items_successful += 1
                    
                except Exception as e:
                    logging.error(f"Failed to save citation: {str(e)}")
                    items_failed += 1

            return IngestionResult(
                success=True,
                items_processed=items_processed,
                items_successful=items_successful,
                items_failed=items_failed,
                metadata={"paper_id": paper_id}
            )

        except Exception as e:
            logging.error(f"Error fetching citations for {paper_id}: {str(e)}")
            return IngestionResult(
                success=False,
                items_processed=0,
                items_successful=0,
                items_failed=1,
                error_message=str(e)
            )
