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

try:
    from analysis.idea_extractor import IdeaExtractor
    SPACY_AVAILABLE = True
except ImportError as e:
    print(f"spaCy not available: {e}")
    SPACY_AVAILABLE = False
    from analysis.idea_extractor_nltk_only import create_nltk_fallback
from storage.database import db_manager
from storage.models import RawData, ExtractedIdea
from config.settings import settings

logger = logging.getLogger(__name__)


class HybridIdeaExtractor(IdeaExtractor):
    """Enhanced idea extractor that combines traditional NLP with AI synthesis."""
    
    def __init__(self, ai_provider: str = "openai"):
        if SPACY_AVAILABLE:
            super().__init__()
        else:
            # Use NLTK fallback
            self.nlp = create_nltk_fallback()
            self.nlp_available = True
        
        self.ai_provider = ai_provider
        
        # Model configuration for different tasks
        self.models = {
            "data_ingestion": "gpt-4o-mini",  # 4o-mini for data ingestion (lower cost)
            "idea_synthesis": "gpt-4o"        # 4o for idea determination (higher quality)
        }
        
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
                    # Test the client with a simple call using 4o-mini
                    test_response = client.chat.completions.create(
                        model=self.models["data_ingestion"],
                        messages=[{"role": "user", "content": "test"}],
                        max_tokens=5
                    )
                    logger.info("OpenAI API client initialized successfully with 4o-mini and 4o models")
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
                
                # Step 1: Traditional sentence extraction (baseline) + AI ingestion
                basic_ideas = []
                ai_ingested_ideas = []
                
                for item in raw_data_items:
                    # Traditional extraction
                    ideas = self._extract_ideas_from_item(item)
                    basic_ideas.extend(ideas)
                    
                    # AI ingestion for individual items (using 4o-mini)
                    if self.ai_client:
                        try:
                            text_content = f"{item.title} {item.abstract or ''}"
                            domain = self._classify_domain(text_content, self.nlp(text_content))
                            if domain:
                                ai_ideas = self._call_ai_for_data_ingestion(text_content, domain)
                                ai_ingested_ideas.extend(ai_ideas)
                        except Exception as e:
                            logger.warning(f"AI ingestion failed for item {item.id}: {e}")
                
                logger.info(f"Extracted {len(basic_ideas)} basic ideas")
                logger.info(f"AI ingested {len(ai_ingested_ideas)} ideas using 4o-mini")
                
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
                all_ideas = basic_ideas + ai_ingested_ideas + synthetic_ideas + pattern_ideas
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
        """Call AI service to generate synthetic ideas using 4o model for high-quality idea determination."""
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

IMPORTANT: Respond ONLY with valid JSON in this exact format:
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

Do not include any other text, only the JSON response.
"""

            response = self.ai_client.chat.completions.create(
                model=self.models["idea_synthesis"],
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
    
    def _call_ai_for_data_ingestion(self, text_content: str, domain: str) -> List[Dict[str, Any]]:
        """Call AI service for data ingestion using 4o-mini model (lower cost)."""
        try:
            prompt = f"""
Analyze this text about {domain.replace('_', ' ')} and extract potential philanthropic intervention ideas:

{text_content[:2000]}  # Limit text length for cost efficiency

Extract 1-2 intervention ideas that:
1. Are directly related to the content
2. Have clear potential for impact
3. Are feasible to implement
4. Address a specific problem or opportunity

For each idea, provide:
- Title: A concise, descriptive title
- Description: Brief explanation of the intervention
- Key Innovation: What makes this approach valuable
- Expected Impact: Specific outcomes and metrics
- Implementation: Key steps to implement
- Challenges: Potential obstacles and solutions

IMPORTANT: Respond ONLY with valid JSON in this exact format:
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

Do not include any other text, only the JSON response.
"""

            response = self.ai_client.chat.completions.create(
                model=self.models["data_ingestion"],
                messages=[
                    {"role": "system", "content": "You are an expert in analyzing research and identifying philanthropic opportunities."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=800  # Lower token limit for cost efficiency
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
                        "confidence_score": 0.7,  # Slightly lower confidence for 4o-mini
                        "extraction_method": "ai_ingestion",
                        "key_innovation": idea.get("key_innovation", ""),
                        "expected_impact": idea.get("expected_impact", ""),
                        "implementation": idea.get("implementation", ""),
                        "challenges": idea.get("challenges", ""),
                        "thought_process": f"AI-ingested idea from {domain} domain using 4o-mini model"
                    }
                    formatted_ideas.append(formatted_idea)
                
                return formatted_ideas
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI ingestion response as JSON")
                return []
                
        except Exception as e:
            logger.error(f"AI data ingestion failed: {e}")
            return []
    
    def _generate_fallback_synthetic_ideas(self, sources: List[RawData]) -> List[Dict[str, Any]]:
        """Generate sophisticated synthetic ideas using enhanced cross-paper analysis."""
        try:
            # Group sources by domain
            domain_groups = self._group_sources_by_domain(sources)
            
            synthetic_ideas = []
            
            for domain, domain_sources in domain_groups.items():
                if len(domain_sources) < 2:
                    continue  # Need multiple sources for synthesis
                
                # Enhanced cross-paper analysis
                cross_paper_insights = self._analyze_cross_paper_context_simple(domain_sources, domain)
                
                # Generate multiple types of synthetic ideas
                ideas = self._generate_contextual_ideas_simple(domain_sources, cross_paper_insights, domain)
                synthetic_ideas.extend(ideas)
            
            return synthetic_ideas
            
        except Exception as e:
            logger.error(f"Failed to generate fallback synthetic ideas: {e}")
            return []
    
    def _analyze_cross_paper_context_simple(self, sources: List[RawData], domain: str) -> Dict[str, Any]:
        """Simple but effective cross-paper context analysis."""
        try:
            # Extract key concepts from each source
            all_keywords = []
            all_titles = []
            all_abstracts = []
            all_concepts = []
            
            for source in sources:
                # Extract keywords from title and abstract
                text_content = f"{source.title} {source.abstract or ''}"
                doc = self.nlp(text_content)
                
                # Extract noun phrases and key terms
                for chunk in doc.noun_chunks:
                    if len(chunk.text.split()) >= 2 and len(chunk.text) < 50:
                        all_keywords.append(chunk.text.lower())
                        all_concepts.append(chunk.text.lower())
                
                # Extract domain-specific keywords
                for keyword in self.enhanced_keywords.get(domain, []):
                    if keyword.lower() in text_content.lower():
                        all_keywords.append(keyword.lower())
                        all_concepts.append(keyword.lower())
                
                all_titles.append(source.title)
                if source.abstract:
                    all_abstracts.append(source.abstract[:200])
            
            # Find common themes and patterns
            from collections import Counter
            keyword_counts = Counter(all_keywords)
            concept_counts = Counter(all_concepts)
            
            # Identify common themes (appearing in multiple sources)
            common_themes = [k for k, v in keyword_counts.items() if v >= 2]
            frequent_concepts = [k for k, v in concept_counts.items() if v >= 2]
            
            # Identify potential gaps (concepts that appear in few sources)
            rare_concepts = [k for k, v in concept_counts.items() if v == 1 and len(k.split()) >= 2]
            
            # Find complementary concepts (appear together in different sources)
            complementary_pairs = []
            for i, source1 in enumerate(sources):
                for j, source2 in enumerate(sources[i+1:], i+1):
                    text1 = f"{source1.title} {source1.abstract or ''}".lower()
                    text2 = f"{source2.title} {source2.abstract or ''}".lower()
                    
                    # Find concepts that appear in both sources
                    concepts1 = set([c for c in all_concepts if c in text1])
                    concepts2 = set([c for c in all_concepts if c in text2])
                    
                    # Find complementary concepts (in one but not the other)
                    complement1 = concepts1 - concepts2
                    complement2 = concepts2 - concepts1
                    
                    if complement1 and complement2:
                        for c1 in list(complement1)[:2]:  # Limit to 2 per source
                            for c2 in list(complement2)[:2]:
                                complementary_pairs.append((c1, c2))
            
            return {
                'common_themes': common_themes,
                'frequent_concepts': frequent_concepts,
                'rare_concepts': rare_concepts,
                'complementary_pairs': complementary_pairs[:5],  # Limit to 5 pairs
                'source_count': len(sources),
                'total_concepts': len(all_concepts),
                'unique_concepts': len(set(all_concepts))
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze cross-paper context: {e}")
            return {}
    
    def _generate_contextual_ideas_simple(self, sources: List[RawData], insights: Dict[str, Any], domain: str) -> List[Dict[str, Any]]:
        """Generate contextual ideas based on simple cross-paper analysis."""
        ideas = []
        
        # Generate theme-based integration ideas
        if insights.get('common_themes'):
            idea = self._generate_theme_integration_idea(insights, domain)
            if idea:
                ideas.append(idea)
        
        # Generate gap-filling ideas
        if insights.get('rare_concepts'):
            idea = self._generate_gap_filling_idea_simple(insights, domain)
            if idea:
                ideas.append(idea)
        
        # Generate complementary synthesis ideas
        if insights.get('complementary_pairs'):
            idea = self._generate_complementary_synthesis_idea(insights, domain)
            if idea:
                ideas.append(idea)
        
        # Generate comprehensive integration idea
        if insights.get('frequent_concepts'):
            idea = self._generate_comprehensive_integration_idea(insights, domain)
            if idea:
                ideas.append(idea)
        
        return ideas
    
    def _generate_theme_integration_idea(self, insights: Dict[str, Any], domain: str) -> Dict[str, Any]:
        """Generate an idea based on common themes across papers."""
        common_themes = insights.get('common_themes', [])
        if not common_themes:
            return None
        
        theme_str = ", ".join(common_themes[:3])
        title = f"Integrated {domain.replace('_', ' ').title()} Approach Using {theme_str.title()}"
        
        description = f"This intervention integrates the most frequently identified themes from {insights['source_count']} related studies in {domain}. "
        description += f"Key elements include: {theme_str}. "
        description += f"Based on cross-paper analysis revealing {len(common_themes)} common themes across multiple {domain} interventions."
        
        return {
            "title": title,
            "description": description,
            "domain": domain,
            "primary_metric": self._get_metric_for_domain(domain),
            "idea_type": "newly_viable",
            "confidence_score": 0.75,
            "extraction_method": "cross_paper_theme_integration",
            "key_innovation": f"Integration of {len(common_themes)} common themes from {insights['source_count']} studies",
            "expected_impact": f"Enhanced outcomes through evidence-based theme integration",
            "implementation": f"Systematic integration of {theme_str} approaches",
            "challenges": "Ensuring proper coordination of multiple thematic elements",
            "thought_process": f"Cross-paper theme analysis: identified {len(common_themes)} common themes across {insights['source_count']} {domain} studies"
        }
    
    def _generate_gap_filling_idea_simple(self, insights: Dict[str, Any], domain: str) -> Dict[str, Any]:
        """Generate an idea to address gaps identified in cross-paper analysis."""
        rare_concepts = insights.get('rare_concepts', [])
        if not rare_concepts:
            return None
        
        # Select a promising rare concept
        rare_concept = rare_concepts[0] if rare_concepts else "novel approach"
        
        title = f"Novel {rare_concept.title()} Intervention for {domain.replace('_', ' ').title()}"
        description = f"This intervention addresses a research gap by focusing on {rare_concept}, which appears in only one of {insights['source_count']} analyzed studies. "
        description += f"This represents an opportunity to explore under-researched approaches in {domain} interventions."
        
        return {
            "title": title,
            "description": description,
            "domain": domain,
            "primary_metric": self._get_metric_for_domain(domain),
            "idea_type": "newly_viable",
            "confidence_score": 0.7,
            "extraction_method": "cross_paper_gap_analysis",
            "key_innovation": f"Focus on under-researched {rare_concept} approach",
            "expected_impact": f"Addresses critical gap in {domain} research",
            "implementation": f"Develop and test {rare_concept} methodology",
            "challenges": f"Limited existing evidence for {rare_concept} approach",
            "thought_process": f"Gap analysis: {rare_concept} appears in only 1 of {insights['source_count']} {domain} studies"
        }
    
    def _generate_complementary_synthesis_idea(self, insights: Dict[str, Any], domain: str) -> Dict[str, Any]:
        """Generate an idea based on complementary concepts from different papers."""
        complementary_pairs = insights.get('complementary_pairs', [])
        if not complementary_pairs:
            return None
        
        # Select a promising complementary pair
        concept1, concept2 = complementary_pairs[0]
        
        title = f"Complementary {concept1.title()}-{concept2.title()} Synthesis for {domain.replace('_', ' ').title()}"
        description = f"This intervention synthesizes complementary approaches: {concept1} and {concept2}. "
        description += f"Cross-paper analysis revealed these concepts appear in different studies but could be combined for enhanced {domain} outcomes."
        
        return {
            "title": title,
            "description": description,
            "domain": domain,
            "primary_metric": self._get_metric_for_domain(domain),
            "idea_type": "newly_viable",
            "confidence_score": 0.8,
            "extraction_method": "cross_paper_complementary_synthesis",
            "key_innovation": f"Synthesis of complementary {concept1} and {concept2} approaches",
            "expected_impact": f"Synergistic effects through complementary concept integration",
            "implementation": f"Sequential or parallel implementation of {concept1} and {concept2}",
            "challenges": "Coordinating timing and integration of complementary approaches",
            "thought_process": f"Complementary analysis: {concept1} and {concept2} appear in different studies but could be combined"
        }
    
    def _generate_comprehensive_integration_idea(self, insights: Dict[str, Any], domain: str) -> Dict[str, Any]:
        """Generate a comprehensive integration idea based on frequent concepts."""
        frequent_concepts = insights.get('frequent_concepts', [])
        if not frequent_concepts:
            return None
        
        concept_str = ", ".join(frequent_concepts[:3])
        
        title = f"Comprehensive {domain.replace('_', ' ').title()} Integration Using {concept_str.title()}"
        description = f"This intervention integrates the most frequently identified concepts from {insights['source_count']} studies: {concept_str}. "
        description += f"Cross-paper analysis shows these concepts appear consistently across multiple {domain} interventions."
        
        return {
            "title": title,
            "description": description,
            "domain": domain,
            "primary_metric": self._get_metric_for_domain(domain),
            "idea_type": "newly_viable",
            "confidence_score": 0.85,
            "extraction_method": "cross_paper_comprehensive_integration",
            "key_innovation": f"Comprehensive integration of {len(frequent_concepts)} frequent concepts",
            "expected_impact": f"Enhanced outcomes through evidence-based comprehensive integration",
            "implementation": f"Systematic integration of {concept_str} approaches",
            "challenges": "Managing complexity of multiple integrated approaches",
            "thought_process": f"Comprehensive analysis: integrated {len(frequent_concepts)} frequent concepts from {insights['source_count']} {domain} studies"
        }
    
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
