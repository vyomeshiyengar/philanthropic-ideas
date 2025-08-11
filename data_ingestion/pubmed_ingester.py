import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import quote_plus

from data_ingestion.base_ingester import BaseDataIngester, IngestionResult
from config.settings import settings

class PubMedIngester(BaseDataIngester):
    def __init__(self):
        source_config = settings.DATA_SOURCES["pubmed"]
        super().__init__("pubmed", source_config)
        self.search_endpoint = source_config["search_endpoint"]
        self.fetch_endpoint = source_config["fetch_endpoint"]
        self.email = "your-email@example.com"  # Required by NCBI for high-volume requests

    async def search(self, query: str, domain: Optional[str] = None, max_results: int = 100) -> IngestionResult:
        """Search PubMed for papers matching the query."""
        try:
            # Step 1: Search for IDs
            search_params = {
                "db": "pubmed",
                "term": query,
                "retmax": min(max_results, 100),  # NCBI limit
                "retmode": "json",
                "email": self.email,
                "tool": "philanthropic-ideas-generator"
            }
            
            search_url = f"{self.base_url}{self.search_endpoint}"
            search_response = await self._make_request(search_url, search_params)
            
            if not search_response:
                return IngestionResult(
                    success=False,
                    items_processed=0,
                    items_successful=0,
                    items_failed=1,
                    error_message="Failed to search PubMed"
                )

            # Extract PMIDs from search response
            pmids = []
            if "esearchresult" in search_response:
                id_list = search_response["esearchresult"].get("idlist", [])
                pmids = id_list[:max_results]
            
            if not pmids:
                return IngestionResult(
                    success=True,
                    items_processed=0,
                    items_successful=0,
                    items_failed=0,
                    metadata={"message": "No results found"}
                )

            # Step 2: Fetch details for each PMID
            items_processed = 0
            items_successful = 0
            items_failed = 0
            
            # Process PMIDs in batches of 20 (NCBI recommendation)
            batch_size = 20
            for i in range(0, len(pmids), batch_size):
                batch_pmids = pmids[i:i + batch_size]
                batch_result = await self._fetch_papers_batch(batch_pmids, domain)
                
                items_processed += batch_result["processed"]
                items_successful += batch_result["successful"]
                items_failed += batch_result["failed"]

            return IngestionResult(
                success=True,
                items_processed=items_processed,
                items_successful=items_successful,
                items_failed=items_failed,
                metadata={"pmids_searched": len(pmids)}
            )

        except Exception as e:
            logging.error(f"Error in PubMed search: {str(e)}")
            return IngestionResult(
                success=False,
                items_processed=0,
                items_successful=0,
                items_failed=1,
                error_message=str(e)
            )

    async def _fetch_papers_batch(self, pmids: List[str], domain: Optional[str] = None) -> Dict[str, int]:
        """Fetch details for a batch of PMIDs."""
        try:
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",
                "rettype": "abstract",
                "email": self.email,
                "tool": "philanthropic-ideas-generator"
            }
            
            fetch_url = f"{self.base_url}{self.fetch_endpoint}"
            fetch_response = await self._make_request(fetch_url, fetch_params)
            
            if not fetch_response:
                return {"processed": len(pmids), "successful": 0, "failed": len(pmids)}

            # Parse XML response
            papers = self._parse_pubmed_xml(fetch_response)
            
            processed = 0
            successful = 0
            failed = 0
            
            for paper in papers:
                processed += 1
                try:
                    # Save to database
                    await self._save_raw_data(
                        content=paper.get("abstract", ""),
                        title=paper.get("title", ""),
                        source_id=paper.get("pmid"),
                        url=f"https://pubmed.ncbi.nlm.nih.gov/{paper.get('pmid')}/",
                        metadata={
                            "authors": paper.get("authors", []),
                            "journal": paper.get("journal", ""),
                            "publication_date": paper.get("publication_date", ""),
                            "keywords": paper.get("keywords", []),
                            "mesh_terms": paper.get("mesh_terms", [])
                        },
                        domain=domain
                    )
                    successful += 1
                except Exception as e:
                    logging.error(f"Failed to save paper {paper.get('pmid')}: {str(e)}")
                    failed += 1

            return {"processed": processed, "successful": successful, "failed": failed}

        except Exception as e:
            logging.error(f"Error fetching PubMed batch: {str(e)}")
            return {"processed": len(pmids), "successful": 0, "failed": len(pmids)}

    def _parse_pubmed_xml(self, xml_content: str) -> List[Dict[str, Any]]:
        """Parse PubMed XML response into structured data."""
        papers = []
        try:
            root = ET.fromstring(xml_content)
            
            for pubmed_article in root.findall(".//PubmedArticle"):
                paper = {}
                
                # Extract PMID
                pmid_elem = pubmed_article.find(".//PMID")
                if pmid_elem is not None:
                    paper["pmid"] = pmid_elem.text
                
                # Extract title
                title_elem = pubmed_article.find(".//ArticleTitle")
                if title_elem is not None:
                    paper["title"] = title_elem.text
                
                # Extract abstract
                abstract_elem = pubmed_article.find(".//AbstractText")
                if abstract_elem is not None:
                    paper["abstract"] = abstract_elem.text
                
                # Extract authors
                authors = []
                for author_elem in pubmed_article.findall(".//Author"):
                    last_name = author_elem.find("LastName")
                    first_name = author_elem.find("ForeName")
                    if last_name is not None and first_name is not None:
                        authors.append(f"{first_name.text} {last_name.text}")
                paper["authors"] = authors
                
                # Extract journal info
                journal_elem = pubmed_article.find(".//Journal/Title")
                if journal_elem is not None:
                    paper["journal"] = journal_elem.text
                
                # Extract publication date
                pub_date_elem = pubmed_article.find(".//PubDate")
                if pub_date_elem is not None:
                    year_elem = pub_date_elem.find("Year")
                    if year_elem is not None:
                        paper["publication_date"] = year_elem.text
                
                # Extract keywords
                keywords = []
                for keyword_elem in pubmed_article.findall(".//Keyword"):
                    if keyword_elem.text:
                        keywords.append(keyword_elem.text)
                paper["keywords"] = keywords
                
                # Extract MeSH terms
                mesh_terms = []
                for mesh_elem in pubmed_article.findall(".//MeshHeading/DescriptorName"):
                    if mesh_elem.text:
                        mesh_terms.append(mesh_elem.text)
                paper["mesh_terms"] = mesh_terms
                
                papers.append(paper)
                
        except Exception as e:
            logging.error(f"Error parsing PubMed XML: {str(e)}")
        
        return papers

    async def search_by_mesh_term(self, mesh_term: str, max_results: int = 100) -> IngestionResult:
        """Search PubMed using MeSH terms."""
        query = f'"{mesh_term}"[MeSH Terms]'
        return await self.search(query, max_results=max_results)

    async def search_recent_papers(self, days: int = 30, max_results: int = 100) -> IngestionResult:
        """Search for recently published papers."""
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = f'("{start_date.strftime("%Y/%m/%d")}"[Date - Publication] : "{end_date.strftime("%Y/%m/%d")}"[Date - Publication])'
        return await self.search(query, max_results=max_results)
