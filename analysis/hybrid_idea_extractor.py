"""
Hybrid idea extraction module that combines traditional NLP with AI-powered synthesis.
"""
import logging
import json
import re
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from collections import defaultdict
import openai
from openai import OpenAI

from analysis.idea_extractor import IdeaExtractor
from storage.database import db_manager
from storage.models import RawData, ExtractedIdea
from config.settings import settings

logger = logging.getLogger(__name__)


class HybridIdeaExtractor(IdeaExtractor):
    """Enhanced idea extractor that combines traditional NLP with AI synthesis."""
    
    def __init__(self, ai_provider: str = "openai"):
        super().__init__()
        self.ai_provider = ai_provider
        self.ai_client = self._initialize_ai_client()
        
        # Enhanced keywords for better clustering
        self.enhanced_keywords = {
            "health": [
                "intervention", "treatment", "prevention", "vaccine", "therapy",
                "clinical trial", "effectiveness", "impact", "outcome", "improvement",
                "reduction", "decrease", "increase", "better", "successful",
                "disease", "mortality", "morbidity", "healthcare", "medical"
            ],
            "education": [
                "learning", "teaching", "pedagogy", "curriculum", "instruction",
                "student", "achievement", "performance", "improvement", "effectiveness",
                "intervention", "program", "initiative", "success", "outcome",
                "school", "education", "literacy", "numeracy", "skills"
            ],
            "economic_development": [
                "poverty", "income", "employment", "job", "entrepreneurship",
                "microfinance", "development", "growth", "improvement", "increase",
                "reduction", "program", "intervention", "effectiveness", "impact",
                "economic", "financial", "business", "market", "trade"
            ],
            "animal_welfare": [
                "animal", "welfare", "suffering", "livestock", "farming",
                "cruelty", "protection", "rights", "improvement", "reduction",
                "intervention", "program", "effectiveness", "impact", "better",
                "wildlife", "conservation", "habitat", "species", "biodiversity"
            ],
            "climate": [
                "climate", "carbon", "emission", "reduction", "mitigation",
                "adaptation", "sustainability", "renewable", "energy", "technology",
                "intervention", "program", "effectiveness", "impact", "improvement",
                "environmental", "green", "clean", "pollution", "conservation"
            ],
            "wellbeing": [
                "wellbeing", "happiness", "mental health", "depression", "anxiety",
                "satisfaction", "quality of life", "improvement", "intervention",
                "therapy", "treatment", "effectiveness", "impact", "better",
                "psychological", "social", "community", "relationships", "support"
            ]
        }
    
    def _initialize_ai_client(self) -> Optional[Any]:
        """Initialize AI client for idea synthesis."""
        try:
            if self.ai_provider == "openai":
                api_key = settings.OPENAI_API_KEY
                if not api_key:
                    logger.info("OpenAI API key not found. AI synthesis will be disabled.")
                    logger.info("The hybrid extractor will work with traditional NLP and pattern recognition.")
                    return None
                
                try:
                    client = OpenAI(api_key=api_key)
                    # Test the client with a simple call
                    test_response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": "test"}],
                        max_tokens=5
                    )
                    logger.info("OpenAI API client initialized successfully")
                    return client
                except Exception as api_error:
                    if "quota" in str(api_error).lower() or "insufficient_quota" in str(api_error).lower():
                        logger.warning("OpenAI API quota exceeded. AI synthesis will be disabled.")
                        logger.info("The hybrid extractor will work with traditional NLP and pattern recognition.")
                    else:
                        logger.warning(f"OpenAI API error: {api_error}. AI synthesis will be disabled.")
                        logger.info("The hybrid extractor will work with traditional NLP and pattern recognition.")
                    return None
            else:
                logger.warning(f"AI provider {self.ai_provider} not supported yet.")
                return None
                
        except Exception as e:
            logger.warning(f"Failed to initialize AI client: {e}")
            logger.info("The hybrid extractor will work with traditional NLP and pattern recognition.")
            return None
    
    def extract_ideas_from_raw_data(self, raw_data_id: Optional[int] = None, 
                                  domain: Optional[str] = None) -> List[Dict[str, Any]]:
        """Enhanced idea extraction using hybrid approach."""
        try:
            with db_manager.get_session() as session:
                # Get raw data
                query = session.query(RawData)
                
                if raw_data_id:
                    query = query.filter(RawData.id == raw_data_id)
                
                if domain:
                    query = query.filter(RawData.metadata_json.contains({"domain": domain}))
                
                raw_data_items = query.all()
                
                if not raw_data_items:
                    logger.info("No raw data found for idea extraction")
                    return []
                
                logger.info(f"Starting hybrid idea extraction from {len(raw_data_items)} items")
                
                # Step 1: Traditional sentence extraction (baseline)
                basic_ideas = []
                for item in raw_data_items:
                    ideas = self._extract_ideas_from_item(item)
                    basic_ideas.extend(ideas)
                
                logger.info(f"Extracted {len(basic_ideas)} basic ideas")
                
                # Step 2: AI synthesis from related sources (optional)
                synthetic_ideas = []
                if self.ai_client:
                    try:
                        synthetic_ideas = self._generate_synthetic_ideas(raw_data_items)
                        logger.info(f"Generated {len(synthetic_ideas)} AI-synthesized ideas")
                    except Exception as e:
                        logger.warning(f"AI synthesis failed: {e}. Continuing with traditional methods.")
                        synthetic_ideas = []
                else:
                    logger.info("AI synthesis not available. Using traditional NLP and pattern recognition.")
                
                # Step 3: Cross-source pattern recognition
                pattern_ideas = self._identify_cross_source_patterns(raw_data_items)
                logger.info(f"Identified {len(pattern_ideas)} pattern-based ideas")
                
                # Step 4: Combine and rank all ideas
                all_ideas = basic_ideas + synthetic_ideas + pattern_ideas
                ranked_ideas = self._rank_and_filter_ideas(all_ideas)
                
                logger.info(f"Final result: {len(ranked_ideas)} high-quality ideas")
                return ranked_ideas
                
        except Exception as e:
            logger.error(f"Failed to extract ideas using hybrid approach: {e}")
            return []
    
    def _generate_synthetic_ideas(self, sources: List[RawData]) -> List[Dict[str, Any]]:
        """Generate synthetic ideas using AI from multiple related sources."""
        if not self.ai_client:
            # Fallback: Generate synthetic ideas using traditional methods
            return self._generate_fallback_synthetic_ideas(sources)
        
        try:
            # Group sources by domain
            domain_groups = self._group_sources_by_domain(sources)
            
            synthetic_ideas = []
            
            for domain, domain_sources in domain_groups.items():
                if len(domain_sources) < 2:
                    continue  # Need multiple sources for synthesis
                
                # Create context from multiple sources
                context = self._create_synthesis_context(domain_sources)
                
                # Generate ideas for this domain
                domain_ideas = self._call_ai_for_synthesis(context, domain)
                synthetic_ideas.extend(domain_ideas)
            
            return synthetic_ideas
            
        except Exception as e:
            logger.error(f"Failed to generate synthetic ideas: {e}")
            return []
    
    def _group_sources_by_domain(self, sources: List[RawData]) -> Dict[str, List[RawData]]:
        """Group sources by their primary domain."""
        domain_groups = defaultdict(list)
        
        for source in sources:
            # Determine domain for this source
            text_content = f"{source.title} {source.abstract or ''}"
            domain = self._classify_domain(text_content, self.nlp(text_content))
            
            if domain:
                domain_groups[domain].append(source)
        
        return dict(domain_groups)
    
    def _create_synthesis_context(self, sources: List[RawData]) -> str:
        """Create context for AI synthesis from multiple sources."""
        context_parts = []
        
        for i, source in enumerate(sources[:5], 1):  # Limit to 5 sources
            context_parts.append(f"Source {i}: {source.title}")
            if source.abstract:
                context_parts.append(f"Abstract: {source.abstract[:300]}...")
        
        return "\n\n".join(context_parts)
    
    def _call_ai_for_synthesis(self, context: str, domain: str) -> List[Dict[str, Any]]:
        """Call AI service to generate synthetic ideas."""
        try:
            prompt = f"""
Based on these related sources about {domain.replace('_', ' ')}:

{context}

Generate 2-3 novel philanthropic intervention ideas that:
1. Combine insights from multiple sources
2. Address gaps not covered by individual sources
3. Are feasible and scalable
4. Have high potential impact

For each idea, provide:
- Title: A concise, descriptive title
- Description: Detailed explanation of the intervention
- Key Innovation: What makes this approach novel
- Expected Impact: Specific outcomes and metrics
- Implementation: Key steps to implement
- Challenges: Potential obstacles and solutions

Format as JSON:
{{
    "ideas": [
        {{
            "title": "Title here",
            "description": "Description here",
            "key_innovation": "Innovation here",
            "expected_impact": "Impact here",
            "implementation": "Implementation here",
            "challenges": "Challenges here"
        }}
    ]
}}
"""

            response = self.ai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert in philanthropic intervention design and effective altruism."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON response
            try:
                data = json.loads(content)
                ideas = data.get("ideas", [])
                
                # Convert to our format
                formatted_ideas = []
                for idea in ideas:
                    formatted_idea = {
                        "title": idea.get("title", ""),
                        "description": idea.get("description", ""),
                        "domain": domain,
                        "primary_metric": self._classify_primary_metric(idea.get("description", ""), domain),
                        "idea_type": "newly_viable",  # AI-generated ideas are typically newly viable
                        "confidence_score": 0.8,  # High confidence for AI-synthesized ideas
                        "extraction_method": "ai_synthesis",
                        "key_innovation": idea.get("key_innovation", ""),
                        "expected_impact": idea.get("expected_impact", ""),
                        "implementation": idea.get("implementation", ""),
                        "challenges": idea.get("challenges", ""),
                        "thought_process": f"AI-synthesized idea combining insights from {len(sources)} related sources in {domain} domain"
                    }
                    formatted_ideas.append(formatted_idea)
                
                return formatted_ideas
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI response as JSON")
                return []
                
        except Exception as e:
            logger.error(f"AI synthesis failed: {e}")
            return []
    
    def _generate_fallback_synthetic_ideas(self, sources: List[RawData]) -> List[Dict[str, Any]]:
        """Generate synthetic ideas using traditional methods when AI is not available."""
        try:
            # Group sources by domain
            domain_groups = self._group_sources_by_domain(sources)
            
            synthetic_ideas = []
            
            for domain, domain_sources in domain_groups.items():
                if len(domain_sources) < 2:
                    continue  # Need multiple sources for synthesis
                
                # Extract key concepts from all sources in this domain
                all_keywords = []
                all_titles = []
                all_abstracts = []
                
                for source in domain_sources:
                    # Extract keywords from title and abstract
                    text_content = f"{source.title} {source.abstract or ''}"
                    doc = self.nlp(text_content)
                    
                    # Extract noun phrases and key terms
                    for chunk in doc.noun_chunks:
                        if len(chunk.text.split()) >= 2 and len(chunk.text) < 50:
                            all_keywords.append(chunk.text.lower())
                    
                    # Extract domain-specific keywords
                    for keyword in self.enhanced_keywords.get(domain, []):
                        if keyword.lower() in text_content.lower():
                            all_keywords.append(keyword.lower())
                    
                    all_titles.append(source.title)
                    if source.abstract:
                        all_abstracts.append(source.abstract[:200])
                
                # Find common themes and gaps
                keyword_counts = {}
                for keyword in all_keywords:
                    keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
                
                # Generate synthetic ideas based on common themes
                common_themes = [k for k, v in keyword_counts.items() if v >= 2]
                
                if common_themes:
                    # Create synthetic idea combining common themes
                    theme_str = ", ".join(common_themes[:3])
                    title = f"Integrated {domain.replace('_', ' ').title()} Intervention Using {theme_str.title()}"
                    
                    description = f"This intervention combines multiple approaches from {len(domain_sources)} related studies in {domain}. "
                    description += f"Key elements include: {theme_str}. "
                    description += f"Based on analysis of {len(all_titles)} research papers, this integrated approach addresses "
                    description += f"gaps identified across multiple studies in the {domain} domain."
                    
                    synthetic_idea = {
                        "title": title,
                        "description": description,
                        "domain": domain,
                        "primary_metric": self._get_metric_for_domain(domain),
                        "idea_type": "newly_viable",
                        "confidence_score": 0.7,  # Good confidence for traditional synthesis
                        "extraction_method": "traditional_synthesis",
                        "key_innovation": f"Integration of {len(domain_sources)} related approaches in {domain}",
                        "expected_impact": f"Enhanced outcomes through combined insights from multiple {domain} studies",
                        "implementation": f"Implement key elements from {len(domain_sources)} related interventions",
                        "challenges": "Coordination of multiple intervention components and measurement of combined effects",
                        "thought_process": f"Traditional synthesis combining insights from {len(domain_sources)} related sources in {domain} domain"
                    }
                    
                    synthetic_ideas.append(synthetic_idea)
            
            return synthetic_ideas
            
        except Exception as e:
            logger.error(f"Failed to generate fallback synthetic ideas: {e}")
            return []
    
    def _identify_cross_source_patterns(self, sources: List[RawData]) -> List[Dict[str, Any]]:
        """Identify patterns across multiple sources to generate ideas."""
        try:
            # Extract key concepts from each source
            all_concepts = []
            for source in sources:
                concepts = self._extract_key_concepts(source)
                all_concepts.extend(concepts)
            
            # Find common themes
            themes = self._cluster_concepts(all_concepts)
            
            # Identify gaps
            gaps = self._identify_research_gaps(themes, sources)
            
            # Generate ideas based on gaps
            pattern_ideas = []
            for gap in gaps:
                idea = self._generate_gap_filling_idea(gap, themes)
                if idea:
                    pattern_ideas.append(idea)
            
            return pattern_ideas
            
        except Exception as e:
            logger.error(f"Failed to identify cross-source patterns: {e}")
            return []
    
    def _extract_key_concepts(self, source: RawData) -> List[str]:
        """Extract key concepts from a source."""
        text_content = f"{source.title} {source.abstract or ''}"
        
        # Use spaCy to extract noun phrases and key terms
        doc = self.nlp(text_content)
        
        concepts = []
        
        # Extract noun phrases
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) >= 2 and len(chunk.text) < 50:
                concepts.append(chunk.text.lower())
        
        # Extract named entities
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PRODUCT", "GPE", "EVENT"]:
                concepts.append(ent.text.lower())
        
        # Extract key terms based on enhanced keywords
        for domain, keywords in self.enhanced_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_content.lower():
                    concepts.append(keyword.lower())
        
        return list(set(concepts))  # Remove duplicates
    
    def _cluster_concepts(self, concepts: List[str]) -> Dict[str, List[str]]:
        """Cluster concepts into themes."""
        themes = defaultdict(list)
        
        # Simple clustering based on domain keywords
        for concept in concepts:
            for domain, keywords in self.enhanced_keywords.items():
                if any(keyword in concept for keyword in keywords):
                    themes[domain].append(concept)
                    break
        
        return dict(themes)
    
    def _identify_research_gaps(self, themes: Dict[str, List[str]], sources: List[RawData]) -> List[Dict[str, Any]]:
        """Identify gaps in current research."""
        gaps = []
        
        # Look for domains with few sources
        domain_counts = defaultdict(int)
        for source in sources:
            text_content = f"{source.title} {source.abstract or ''}"
            domain = self._classify_domain(text_content, self.nlp(text_content))
            if domain:
                domain_counts[domain] += 1
        
        # Identify underrepresented areas
        for domain, keywords in self.enhanced_keywords.items():
            if domain_counts[domain] < 2:  # Few sources
                gaps.append({
                    "type": "underrepresented_domain",
                    "domain": domain,
                    "description": f"Limited research in {domain} domain",
                    "keywords": keywords[:5]
                })
        
        # Look for missing cross-domain connections
        for domain1 in themes:
            for domain2 in themes:
                if domain1 != domain2:
                    # Check if there are cross-domain applications
                    cross_domain_keywords = set(themes[domain1]) & set(themes[domain2])
                    if len(cross_domain_keywords) > 0:
                        gaps.append({
                            "type": "cross_domain_opportunity",
                            "domains": [domain1, domain2],
                            "description": f"Cross-domain opportunity between {domain1} and {domain2}",
                            "keywords": list(cross_domain_keywords)
                        })
        
        return gaps
    
    def _generate_gap_filling_idea(self, gap: Dict[str, Any], themes: Dict[str, List[str]]) -> Optional[Dict[str, Any]]:
        """Generate an idea to fill a research gap."""
        try:
            if gap["type"] == "underrepresented_domain":
                domain = gap["domain"]
                keywords = gap["keywords"]
                
                # Generate idea based on keywords
                title = f"Comprehensive {domain.replace('_', ' ').title()} Intervention Program"
                description = f"This intervention focuses on addressing the gap in {domain} research by implementing a comprehensive program using {', '.join(keywords[:3])}. Key metrics: {self._get_metric_for_domain(domain)}. Expected impact: significant improvement in {domain} outcomes."
                
                return {
                    "title": title,
                    "description": description,
                    "domain": domain,
                    "primary_metric": self._get_metric_for_domain(domain),
                    "idea_type": "evergreen",  # Gap-filling ideas are often evergreen
                    "confidence_score": 0.6,
                    "extraction_method": "pattern_recognition",
                    "thought_process": f"Identified gap in {domain} domain with limited research coverage"
                }
            
            elif gap["type"] == "cross_domain_opportunity":
                domains = gap["domains"]
                keywords = gap["keywords"]
                
                title = f"Cross-Domain {domains[0].title()}-{domains[1].title()} Integration"
                description = f"This intervention leverages synergies between {domains[0]} and {domains[1]} domains using {', '.join(keywords[:3])}. Key metrics: {self._get_metric_for_domain(domains[0])}. Expected impact: enhanced outcomes through cross-domain collaboration."
                
                return {
                    "title": title,
                    "description": description,
                    "domain": domains[0],  # Primary domain
                    "primary_metric": self._get_metric_for_domain(domains[0]),
                    "idea_type": "newly_viable",
                    "confidence_score": 0.7,
                    "extraction_method": "pattern_recognition",
                    "thought_process": f"Identified cross-domain opportunity between {domains[0]} and {domains[1]}"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to generate gap-filling idea: {e}")
            return None
    
    def _get_metric_for_domain(self, domain: str) -> str:
        """Get the primary metric for a domain."""
        metric_mapping = {
            "health": "DALYs (Disability-Adjusted Life Years)",
            "education": "Log income (correlates with educational outcomes)",
            "economic_development": "Log income (direct economic impact)",
            "animal_welfare": "WALYs (Welfare-Adjusted Life Years)",
            "climate": "CO2-equivalent reduction",
            "wellbeing": "WELBYs (Wellbeing-Adjusted Life Years)"
        }
        return metric_mapping.get(domain, "WELBYs (general wellbeing)")
    
    def _rank_and_filter_ideas(self, ideas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank and filter ideas based on quality and uniqueness."""
        try:
            # Remove duplicates based on title similarity
            unique_ideas = self._remove_duplicate_ideas(ideas)
            
            # Score ideas based on multiple factors
            scored_ideas = []
            for idea in unique_ideas:
                score = self._calculate_enhanced_score(idea)
                idea["enhanced_score"] = score
                scored_ideas.append(idea)
            
            # Sort by enhanced score
            scored_ideas.sort(key=lambda x: x["enhanced_score"], reverse=True)
            
            # Return top ideas
            return scored_ideas[:50]  # Limit to top 50 ideas
            
        except Exception as e:
            logger.error(f"Failed to rank and filter ideas: {e}")
            return ideas
    
    def _remove_duplicate_ideas(self, ideas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate ideas based on title similarity."""
        unique_ideas = []
        seen_titles = set()
        
        for idea in ideas:
            title = idea.get("title", "").lower()
            
            # Check if this title is too similar to existing ones
            is_duplicate = False
            for seen_title in seen_titles:
                similarity = self._calculate_title_similarity(title, seen_title)
                if similarity > 0.8:  # 80% similarity threshold
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_ideas.append(idea)
                seen_titles.add(title)
        
        return unique_ideas
    
    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles."""
        words1 = set(title1.split())
        words2 = set(title2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def _calculate_enhanced_score(self, idea: Dict[str, Any]) -> float:
        """Calculate enhanced score for idea ranking."""
        score = 0.0
        
        # Base confidence score
        confidence = idea.get("confidence_score", 0.5)
        score += confidence * 0.3
        
        # Method bonus (AI synthesis gets higher score)
        method = idea.get("extraction_method", "nlp")
        if method == "ai_synthesis":
            score += 0.2
        elif method == "pattern_recognition":
            score += 0.1
        
        # Length and quality indicators
        title = idea.get("title", "")
        description = idea.get("description", "")
        
        if len(title) > 10 and len(title) < 100:
            score += 0.1
        
        if len(description) > 50:
            score += 0.1
        
        # Domain-specific scoring
        domain = idea.get("domain", "")
        if domain in ["health", "climate"]:  # High-impact domains
            score += 0.1
        
        # Idea type scoring
        idea_type = idea.get("idea_type", "")
        if idea_type == "newly_viable":
            score += 0.1
        
        return min(score, 1.0)
    
    def save_extracted_ideas(self, ideas: List[Dict[str, Any]]) -> int:
        """Save extracted ideas to the database with enhanced metadata."""
        saved_count = 0
        
        try:
            with db_manager.get_session() as session:
                for idea_data in ideas:
                    # Create ExtractedIdea object
                    extracted_idea = ExtractedIdea(
                        raw_data_id=idea_data.get("raw_data_id"),
                        title=idea_data.get("title", "")[:500],
                        description=idea_data.get("description", ""),
                        domain=idea_data.get("domain", ""),
                        primary_metric=idea_data.get("primary_metric", ""),
                        idea_type=idea_data.get("idea_type", ""),
                        confidence_score=idea_data.get("confidence_score", 0.5),
                        extraction_method=idea_data.get("extraction_method", "hybrid"),
                        thought_process=idea_data.get("thought_process", ""),
                        created_at=datetime.utcnow()
                    )
                    
                    session.add(extracted_idea)
                    saved_count += 1
                
                session.commit()
                logger.info(f"Saved {saved_count} hybrid-extracted ideas to database")
                
        except Exception as e:
            logger.error(f"Failed to save extracted ideas: {e}")
        
        return saved_count
