"""
Talent identification module for finding people to work on philanthropic ideas.
"""
import logging
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
import re

from storage.database import db_manager
from storage.models import ExtractedIdea, TalentProfile, IdeaTalentMatch
from config.settings import settings

logger = logging.getLogger(__name__)


class TalentIdentifier:
    """Identifies potential talent for philanthropic ideas."""
    
    def __init__(self):
        self.google_api_key = settings.GOOGLE_API_KEY
        
        # Domain to expertise mapping
        self.domain_expertise_mapping = {
            "health": [
                "public health", "epidemiology", "medicine", "clinical research",
                "healthcare", "biotechnology", "pharmaceuticals", "global health"
            ],
            "education": [
                "education", "pedagogy", "curriculum development", "educational technology",
                "learning science", "teacher training", "early childhood education"
            ],
            "economic_development": [
                "economic development", "poverty alleviation", "microfinance",
                "entrepreneurship", "job creation", "skills training", "development economics"
            ],
            "animal_welfare": [
                "animal welfare", "veterinary medicine", "animal rights", "livestock",
                "wildlife conservation", "animal behavior", "farming"
            ],
            "climate": [
                "climate change", "carbon removal", "renewable energy", "sustainability",
                "environmental science", "clean technology", "climate policy"
            ],
            "wellbeing": [
                "mental health", "psychology", "happiness research", "wellbeing",
                "social work", "counseling", "positive psychology"
            ]
        }
        
        # Role types for different domains
        self.role_types = {
            "health": ["researcher", "practitioner", "policy maker", "entrepreneur"],
            "education": ["educator", "researcher", "curriculum developer", "entrepreneur"],
            "economic_development": ["economist", "practitioner", "entrepreneur", "policy maker"],
            "animal_welfare": ["veterinarian", "researcher", "advocate", "entrepreneur"],
            "climate": ["scientist", "engineer", "policy maker", "entrepreneur"],
            "wellbeing": ["psychologist", "researcher", "practitioner", "entrepreneur"]
        }
    
    async def identify_talent_for_idea(self, idea_id: int, max_candidates: int = 5) -> List[Dict[str, Any]]:
        """Identify potential talent for a specific idea."""
        try:
            with db_manager.get_session() as session:
                idea = session.query(ExtractedIdea).filter(ExtractedIdea.id == idea_id).first()
                
                if not idea:
                    logger.error(f"Idea {idea_id} not found")
                    return []
                
                # Get expertise areas for the domain
                expertise_areas = self.domain_expertise_mapping.get(idea.domain, [])
                
                # Search for talent
                candidates = []
                
                # Search web (Google Search API only)
                web_candidates = await self._search_web(
                    idea.title, expertise_areas, max_candidates
                )
                candidates.extend(web_candidates)
                
                # Score and rank candidates
                scored_candidates = []
                for candidate in candidates:
                    score = self._calculate_fit_score(candidate, idea)
                    candidate["fit_score"] = score
                    scored_candidates.append(candidate)
                
                # Sort by fit score
                scored_candidates.sort(key=lambda x: x["fit_score"], reverse=True)
                
                # Save top candidates to database
                top_candidates = scored_candidates[:max_candidates]
                saved_candidates = []
                
                for candidate in top_candidates:
                    talent_profile = self._save_talent_profile(candidate)
                    if talent_profile:
                        match = self._create_idea_talent_match(idea_id, talent_profile.id, candidate)
                        if match:
                            saved_candidates.append({
                                "talent_profile": talent_profile,
                                "match": match,
                                "fit_score": candidate["fit_score"]
                            })
                
                logger.info(f"Identified {len(saved_candidates)} talent candidates for idea {idea_id}")
                return saved_candidates
                
        except Exception as e:
            logger.error(f"Failed to identify talent for idea {idea_id}: {e}")
            return []
    
    async def _search_crunchbase(self, idea_title: str, expertise_areas: List[str], 
                               max_results: int) -> List[Dict[str, Any]]:
        """Search Crunchbase for potential talent (disabled for prototype)."""
        # Crunchbase search disabled for prototype
        logger.info("Crunchbase search disabled for prototype - using Google Search API only")
        return []
    
    async def _search_web(self, idea_title: str, expertise_areas: List[str], 
                         max_results: int) -> List[Dict[str, Any]]:
        """Search web for potential talent using Google Custom Search API."""
        candidates = []
        
        if not settings.GOOGLE_API_KEY:
            logger.warning("Google API key not available")
            return candidates
        
        if not settings.GOOGLE_CUSTOM_SEARCH_ENGINE_ID:
            logger.warning("Google Custom Search Engine ID not available")
            return candidates
        
        try:
            import aiohttp
            
            # Google Custom Search API endpoint
            base_url = "https://www.googleapis.com/customsearch/v1"
            
            # Search for people working in relevant areas
            for expertise in expertise_areas[:3]:
                search_query = f'"{expertise}" "{idea_title.split()[0]}" expert researcher professor'
                
                params = {
                    "key": settings.GOOGLE_API_KEY,
                    "cx": settings.GOOGLE_CUSTOM_SEARCH_ENGINE_ID,
                    "q": search_query,
                    "num": min(10, max_results),  # Google CSE allows max 10 results per query
                    "searchType": "web",
                    "fields": "items(title,snippet,link)"
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(base_url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if "items" in data:
                                for item in data["items"]:
                                    # Extract information from search result
                                    title = item.get("title", "")
                                    snippet = item.get("snippet", "")
                                    link = item.get("link", "")
                                    
                                    # Parse the result to extract candidate information
                                    candidate = self._parse_search_result(title, snippet, link, expertise)
                                    
                                    if candidate:
                                        candidates.append(candidate)
                                        
                                        if len(candidates) >= max_results:
                                            break
                        else:
                            logger.warning(f"Google Custom Search API returned status {response.status}")
                
                # Add delay to respect rate limits
                await asyncio.sleep(1)
                
                if len(candidates) >= max_results:
                    break
        
        except Exception as e:
            logger.error(f"Web search failed: {e}")
        
        return candidates
    
    def _parse_search_result(self, title: str, snippet: str, link: str, expertise: str) -> Optional[Dict[str, Any]]:
        """Parse a Google search result to extract candidate information."""
        try:
            # Extract name from title or snippet
            name = self._extract_name_from_text(title, snippet)
            if not name:
                return None
            
            # Extract organization
            organization = self._extract_organization_from_text(title, snippet, link)
            
            # Extract title/position
            position = self._extract_position_from_text(title, snippet)
            
            # Extract location
            location = self._extract_location_from_text(title, snippet)
            
            # Estimate experience years based on context
            experience_years = self._estimate_experience_years(title, snippet)
            
            # Extract education
            education = self._extract_education_from_text(title, snippet)
            
            # Calculate confidence score based on information quality
            confidence_score = self._calculate_confidence_score(title, snippet, link)
            
            return {
                "name": name,
                "title": position,
                "organization": organization,
                "location": location,
                "expertise_areas": [expertise],
                "experience_years": experience_years,
                "education": education,
                "source": "google_custom_search",
                "source_url": link,
                "confidence_score": confidence_score
            }
            
        except Exception as e:
            logger.debug(f"Failed to parse search result: {e}")
            return None
    
    def _extract_name_from_text(self, title: str, snippet: str) -> Optional[str]:
        """Extract person name from title or snippet."""
        import re
        
        # Common patterns for academic/professional names
        patterns = [
            r"Dr\.\s+([A-Z][a-z]+ [A-Z][a-z]+)",
            r"Professor\s+([A-Z][a-z]+ [A-Z][a-z]+)",
            r"Prof\.\s+([A-Z][a-z]+ [A-Z][a-z]+)",
            r"([A-Z][a-z]+ [A-Z][a-z]+)\s+\(PhD\)",
            r"([A-Z][a-z]+ [A-Z][a-z]+)\s+at\s+",
            r"([A-Z][a-z]+ [A-Z][a-z]+)\s+from\s+"
        ]
        
        text = f"{title} {snippet}"
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        # Fallback: look for capitalized words that might be names
        words = text.split()
        for i, word in enumerate(words):
            if (word[0].isupper() and len(word) > 2 and 
                i + 1 < len(words) and words[i + 1][0].isupper() and len(words[i + 1]) > 2):
                return f"{word} {words[i + 1]}"
        
        return None
    
    def _extract_organization_from_text(self, title: str, snippet: str, link: str) -> str:
        """Extract organization from text."""
        import re
        
        # Common university/organization patterns
        patterns = [
            r"at\s+([A-Z][a-zA-Z\s&]+(?:University|Institute|College|Foundation|Center))",
            r"from\s+([A-Z][a-zA-Z\s&]+(?:University|Institute|College|Foundation|Center))",
            r"([A-Z][a-zA-Z\s&]+(?:University|Institute|College|Foundation|Center))"
        ]
        
        text = f"{title} {snippet}"
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        # Try to extract from URL
        if "edu" in link:
            domain = link.split("//")[1].split("/")[0]
            return domain.replace("www.", "").replace(".edu", " University")
        
        return "Unknown Organization"
    
    def _extract_position_from_text(self, title: str, snippet: str) -> str:
        """Extract position/title from text."""
        positions = [
            "Professor", "Associate Professor", "Assistant Professor", "Lecturer",
            "Researcher", "Research Scientist", "Principal Investigator",
            "Director", "Manager", "Consultant", "Expert"
        ]
        
        text = f"{title} {snippet}".lower()
        
        for position in positions:
            if position.lower() in text:
                return position
        
        return "Researcher"
    
    def _extract_location_from_text(self, title: str, snippet: str) -> str:
        """Extract location from text."""
        import re
        
        # Common location patterns
        patterns = [
            r"([A-Z][a-z]+,\s*[A-Z]{2})",  # City, State
            r"([A-Z][a-z]+,\s*[A-Z][a-z]+)",  # City, Country
            r"([A-Z][a-z]+ University)"  # University name often indicates location
        ]
        
        text = f"{title} {snippet}"
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return "Unknown Location"
    
    def _estimate_experience_years(self, title: str, snippet: str) -> int:
        """Estimate experience years based on context."""
        text = f"{title} {snippet}".lower()
        
        # Look for experience indicators
        if "senior" in text or "principal" in text or "full professor" in text:
            return 15
        elif "associate professor" in text:
            return 10
        elif "assistant professor" in text or "postdoc" in text:
            return 5
        elif "phd" in text or "doctorate" in text:
            return 8
        elif "masters" in text or "ms" in text:
            return 3
        else:
            return 5  # Default estimate
    
    def _extract_education_from_text(self, title: str, snippet: str) -> List[str]:
        """Extract education information from text."""
        education = []
        text = f"{title} {snippet}".lower()
        
        if "phd" in text or "doctorate" in text:
            education.append("PhD")
        if "masters" in text or "ms" in text or "ma" in text:
            education.append("Masters")
        if "bachelors" in text or "ba" in text or "bs" in text:
            education.append("Bachelors")
        
        return education if education else ["Unknown"]
    
    def _calculate_confidence_score(self, title: str, snippet: str, link: str) -> float:
        """Calculate confidence score based on information quality."""
        score = 0.5  # Base score
        
        # Higher score for academic domains
        if any(domain in link for domain in [".edu", "scholar.google.com", "researchgate.net"]):
            score += 0.2
        
        # Higher score for longer, more detailed snippets
        if len(snippet) > 100:
            score += 0.1
        
        # Higher score for professional titles
        if any(title_word in title.lower() for title_word in ["professor", "dr.", "researcher"]):
            score += 0.1
        
        # Higher score for organization mentions
        if any(org_word in snippet.lower() for org_word in ["university", "institute", "foundation"]):
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_fit_score(self, candidate: Dict[str, Any], idea: ExtractedIdea) -> float:
        """Calculate how well a candidate fits the idea."""
        score = 0.0
        
        # Experience relevance
        if candidate.get("experience_years", 0) >= 10:
            score += 2.0
        elif candidate.get("experience_years", 0) >= 5:
            score += 1.0
        
        # Expertise relevance
        candidate_expertise = candidate.get("expertise_areas", [])
        domain_expertise = self.domain_expertise_mapping.get(idea.domain, [])
        
        expertise_overlap = len(set(candidate_expertise) & set(domain_expertise))
        score += expertise_overlap * 1.5
        
        # Organization relevance
        organization = candidate.get("organization", "").lower()
        if any(keyword in organization for keyword in ["research", "university", "institute", "foundation"]):
            score += 1.0
        
        # Education relevance
        education = candidate.get("education", [])
        if any("PhD" in edu for edu in education):
            score += 1.0
        
        # Confidence score
        confidence = candidate.get("confidence_score", 0.5)
        score += confidence * 2.0
        
        return min(score, 10.0)
    
    def _save_talent_profile(self, candidate: Dict[str, Any]) -> Optional[TalentProfile]:
        """Save a talent profile to the database."""
        try:
            with db_manager.get_session() as session:
                # Check if profile already exists
                existing = session.query(TalentProfile).filter(
                    TalentProfile.name == candidate["name"],
                    TalentProfile.organization == candidate.get("organization", "")
                ).first()
                
                if existing:
                    return existing
                
                # Create new profile
                talent_profile = TalentProfile(
                    name=candidate["name"],
                    title=candidate.get("title", ""),
                    organization=candidate.get("organization", ""),
                    location=candidate.get("location", ""),
                    expertise_areas=candidate.get("expertise_areas", []),
                    experience_years=candidate.get("experience_years", 0),
                    education=candidate.get("education", []),
                    source=candidate.get("source", "unknown"),
                    source_url=candidate.get("source_url", ""),
                    confidence_score=candidate.get("confidence_score", 0.5)
                )
                
                session.add(talent_profile)
                session.commit()
                session.refresh(talent_profile)
                
                return talent_profile
                
        except Exception as e:
            logger.error(f"Failed to save talent profile: {e}")
            return None
    
    def _create_idea_talent_match(self, idea_id: int, talent_id: int, 
                                candidate: Dict[str, Any]) -> Optional[IdeaTalentMatch]:
        """Create an idea-talent match record."""
        try:
            with db_manager.get_session() as session:
                # Check if match already exists
                existing = session.query(IdeaTalentMatch).filter(
                    IdeaTalentMatch.idea_id == idea_id,
                    IdeaTalentMatch.talent_id == talent_id
                ).first()
                
                if existing:
                    return existing
                
                # Create new match
                match = IdeaTalentMatch(
                    idea_id=idea_id,
                    talent_id=talent_id,
                    fit_score=candidate["fit_score"],
                    experience_relevance=candidate.get("fit_score", 0) * 0.8,
                    background_relevance=candidate.get("fit_score", 0) * 0.6,
                    match_reasoning=f"Expertise in {', '.join(candidate.get('expertise_areas', []))}",
                    potential_role="Lead Researcher/Implementer"
                )
                
                session.add(match)
                session.commit()
                session.refresh(match)
                
                return match
                
        except Exception as e:
            logger.error(f"Failed to create idea-talent match: {e}")
            return None
    
    async def identify_talent_for_top_ideas(self, top_ideas: List[Dict[str, Any]], 
                                          candidates_per_idea: int = 2) -> Dict[str, Any]:
        """Identify talent for the top ideas."""
        results = {
            "total_ideas": len(top_ideas),
            "ideas_with_talent": 0,
            "total_candidates": 0,
            "talent_by_idea": {}
        }
        
        for idea in top_ideas:
            try:
                idea_id = idea["idea_id"]
                candidates = await self.identify_talent_for_idea(idea_id, candidates_per_idea)
                
                if candidates:
                    results["ideas_with_talent"] += 1
                    results["total_candidates"] += len(candidates)
                    results["talent_by_idea"][idea_id] = candidates
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed to identify talent for idea {idea.get('idea_id')}: {e}")
        
        logger.info(f"Identified talent for {results['ideas_with_talent']} ideas, "
                   f"{results['total_candidates']} total candidates")
        
        return results
    
    def get_talent_for_idea(self, idea_id: int) -> List[Dict[str, Any]]:
        """Get talent profiles for a specific idea."""
        try:
            with db_manager.get_session() as session:
                matches = session.query(IdeaTalentMatch, TalentProfile).join(
                    TalentProfile, IdeaTalentMatch.talent_id == TalentProfile.id
                ).filter(IdeaTalentMatch.idea_id == idea_id).order_by(
                    IdeaTalentMatch.fit_score.desc()
                ).all()
                
                results = []
                for match, talent in matches:
                    results.append({
                        "talent_id": talent.id,
                        "name": talent.name,
                        "title": talent.title,
                        "organization": talent.organization,
                        "location": talent.location,
                        "expertise_areas": talent.expertise_areas,
                        "experience_years": talent.experience_years,
                        "education": talent.education,
                        "fit_score": match.fit_score,
                        "match_reasoning": match.match_reasoning,
                        "potential_role": match.potential_role,
                        "source": talent.source,
                        "source_url": talent.source_url
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Failed to get talent for idea {idea_id}: {e}")
            return []
    
    def search_talent_by_expertise(self, expertise: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search for talent by expertise area."""
        try:
            with db_manager.get_session() as session:
                # Search for talent profiles with matching expertise
                talent_profiles = session.query(TalentProfile).filter(
                    TalentProfile.expertise_areas.contains([expertise])
                ).order_by(TalentProfile.experience_years.desc()).limit(max_results).all()
                
                results = []
                for talent in talent_profiles:
                    results.append({
                        "talent_id": talent.id,
                        "name": talent.name,
                        "title": talent.title,
                        "organization": talent.organization,
                        "location": talent.location,
                        "expertise_areas": talent.expertise_areas,
                        "experience_years": talent.experience_years,
                        "education": talent.education,
                        "source": talent.source,
                        "source_url": talent.source_url,
                        "confidence_score": talent.confidence_score
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Failed to search talent by expertise: {e}")
            return []
    
    def get_talent_statistics(self) -> Dict[str, Any]:
        """Get statistics about talent profiles in the database."""
        try:
            with db_manager.get_session() as session:
                total_talent = session.query(TalentProfile).count()
                
                # Count by source
                sources = session.query(TalentProfile.source).distinct().all()
                source_counts = {}
                for source in sources:
                    count = session.query(TalentProfile).filter(
                        TalentProfile.source == source[0]
                    ).count()
                    source_counts[source[0]] = count
                
                # Count by expertise area
                all_expertise = []
                talent_profiles = session.query(TalentProfile).all()
                for talent in talent_profiles:
                    if talent.expertise_areas:
                        all_expertise.extend(talent.expertise_areas)
                
                expertise_counts = {}
                for expertise in set(all_expertise):
                    expertise_counts[expertise] = all_expertise.count(expertise)
                
                # Sort expertise by count
                expertise_counts = dict(sorted(expertise_counts.items(), 
                                             key=lambda x: x[1], reverse=True))
                
                return {
                    "total_talent": total_talent,
                    "by_source": source_counts,
                    "by_expertise": expertise_counts,
                    "top_expertise": dict(list(expertise_counts.items())[:10])
                }
                
        except Exception as e:
            logger.error(f"Failed to get talent statistics: {e}")
            return {}
