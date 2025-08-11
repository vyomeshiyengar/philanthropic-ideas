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
        """Search the web for potential talent."""
        candidates = []
        
        if not self.google_api_key:
            logger.warning("Google API key not available")
            return candidates
        
        try:
            # Search for people working in relevant areas
            for expertise in expertise_areas[:3]:
                search_query = f'"{expertise}" "{idea_title.split()[0]}" expert researcher'
                
                # This is a simplified version - in practice you'd use the Google Custom Search API
                # For now, we'll create mock candidates
                mock_candidate = {
                    "name": f"Prof. {expertise.title()} Specialist",
                    "title": f"Professor of {expertise.title()}",
                    "organization": f"{expertise.title()} University",
                    "location": "Cambridge, MA",
                    "expertise_areas": [expertise],
                    "experience_years": 20,
                    "education": ["PhD in " + expertise.title()],
                    "source": "web_search",
                    "source_url": f"https://scholar.google.com/citations?user={expertise.lower()}",
                    "confidence_score": 0.7
                }
                
                candidates.append(mock_candidate)
                
                if len(candidates) >= max_results:
                    break
        
        except Exception as e:
            logger.error(f"Web search failed: {e}")
        
        return candidates
    
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
