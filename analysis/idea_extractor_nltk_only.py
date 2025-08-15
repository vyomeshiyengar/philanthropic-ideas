"""
NLTK-Only Idea Extractor - spaCy-free version for Mac Python 3.12 compatibility
"""
import re
import logging
from typing import List, Dict, Any, Optional
from collections import Counter
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords, wordnet
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk
import string

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NLTKIdeaExtractor:
    """NLTK-only idea extractor for Mac Python 3.12 compatibility."""
    
    def __init__(self):
        """Initialize the NLTK-only extractor."""
        self.stop_words = set(stopwords.words('english'))
        self.nlp_available = True
        
        # Ensure NLTK data is available
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
            nltk.data.find('corpora/wordnet')
            nltk.data.find('taggers/averaged_perceptron_tagger')
            nltk.data.find('chunkers/maxent_ne_chunker')
            nltk.data.find('corpora/words')
        except LookupError:
            logger.warning("NLTK data not found. Downloading...")
            nltk.download('punkt')
            nltk.download('stopwords')
            nltk.download('wordnet')
            nltk.download('averaged_perceptron_tagger')
            nltk.download('maxent_ne_chunker')
            nltk.download('words')
    
    def _classify_domain(self, text: str, doc=None) -> str:
        """Classify the domain of the text using NLTK."""
        # Domain keywords
        domain_keywords = {
            'health': ['health', 'medical', 'disease', 'treatment', 'patient', 'clinical', 'therapy', 'medicine', 'healthcare', 'hospital'],
            'environment': ['environment', 'climate', 'sustainability', 'green', 'renewable', 'energy', 'pollution', 'conservation', 'ecosystem'],
            'education': ['education', 'learning', 'teaching', 'student', 'school', 'university', 'academic', 'curriculum', 'pedagogy'],
            'technology': ['technology', 'software', 'hardware', 'digital', 'computer', 'algorithm', 'data', 'artificial', 'intelligence'],
            'social': ['social', 'community', 'poverty', 'inequality', 'justice', 'humanitarian', 'welfare', 'development'],
            'research': ['research', 'study', 'analysis', 'investigation', 'experiment', 'methodology', 'scientific']
        }
        
        # Tokenize and normalize text
        tokens = word_tokenize(text.lower())
        tokens = [token for token in tokens if token.isalnum()]
        
        # Count domain keywords
        domain_scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for token in tokens if token in keywords)
            domain_scores[domain] = score
        
        # Return domain with highest score, default to 'general'
        if domain_scores:
            best_domain = max(domain_scores, key=domain_scores.get)
            if domain_scores[best_domain] > 0:
                return best_domain
        
        return 'general'
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases using NLTK."""
        # Tokenize sentences
        sentences = sent_tokenize(text)
        key_phrases = []
        
        for sentence in sentences:
            # Tokenize and POS tag
            tokens = word_tokenize(sentence)
            pos_tags = pos_tag(tokens)
            
            # Extract noun phrases (simplified)
            noun_phrases = []
            current_phrase = []
            
            for token, pos in pos_tags:
                if pos.startswith('NN'):  # Noun
                    current_phrase.append(token)
                else:
                    if current_phrase:
                        noun_phrases.append(' '.join(current_phrase))
                        current_phrase = []
            
            if current_phrase:
                noun_phrases.append(' '.join(current_phrase))
            
            # Add meaningful phrases
            for phrase in noun_phrases:
                if len(phrase.split()) >= 2 and len(phrase) > 5:
                    key_phrases.append(phrase)
        
        return key_phrases
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities using NLTK."""
        try:
            tokens = word_tokenize(text)
            pos_tags = pos_tag(tokens)
            named_entities = ne_chunk(pos_tags)
            
            entities = []
            for chunk in named_entities:
                if hasattr(chunk, 'label'):
                    entity = ' '.join(c[0] for c in chunk)
                    entities.append(entity)
            
            return entities
        except Exception as e:
            logger.warning(f"Entity extraction failed: {e}")
            return []
    
    def _generate_ideas_from_text(self, text: str, domain: str) -> List[Dict[str, Any]]:
        """Generate ideas from text using NLTK."""
        ideas = []
        
        # Extract key phrases
        key_phrases = self._extract_key_phrases(text)
        
        # Extract entities
        entities = self._extract_entities(text)
        
        # Generate ideas based on key phrases
        for phrase in key_phrases[:10]:  # Limit to top 10 phrases
            if len(phrase.split()) >= 2:
                idea = {
                    'title': f"Research on {phrase}",
                    'description': f"Investigate and develop solutions related to {phrase}",
                    'domain': domain,
                    'confidence': 0.6,
                    'source': 'key_phrase_extraction',
                    'key_phrases': [phrase]
                }
                ideas.append(idea)
        
        # Generate ideas based on entities
        for entity in entities[:5]:  # Limit to top 5 entities
            idea = {
                'title': f"Study of {entity}",
                'description': f"Conduct research on {entity} and its applications",
                'domain': domain,
                'confidence': 0.7,
                'source': 'entity_extraction',
                'key_phrases': [entity]
            }
            ideas.append(idea)
        
        # Generate domain-specific ideas
        domain_ideas = self._generate_domain_specific_ideas(domain, key_phrases)
        ideas.extend(domain_ideas)
        
        return ideas
    
    def _generate_domain_specific_ideas(self, domain: str, key_phrases: List[str]) -> List[Dict[str, Any]]:
        """Generate domain-specific ideas."""
        ideas = []
        
        domain_templates = {
            'health': [
                "Develop new treatment for {topic}",
                "Improve diagnosis methods for {topic}",
                "Create prevention strategies for {topic}",
                "Enhance patient care through {topic}"
            ],
            'environment': [
                "Develop sustainable solutions for {topic}",
                "Create renewable energy systems for {topic}",
                "Implement conservation strategies for {topic}",
                "Reduce environmental impact of {topic}"
            ],
            'education': [
                "Improve learning methods for {topic}",
                "Develop educational tools for {topic}",
                "Create curriculum enhancements for {topic}",
                "Enhance student engagement with {topic}"
            ],
            'technology': [
                "Develop AI solutions for {topic}",
                "Create software tools for {topic}",
                "Implement automation for {topic}",
                "Build digital platforms for {topic}"
            ],
            'social': [
                "Address social issues related to {topic}",
                "Create community programs for {topic}",
                "Develop support systems for {topic}",
                "Improve access to {topic}"
            ]
        }
        
        templates = domain_templates.get(domain, [
            "Research and develop solutions for {topic}",
            "Create innovative approaches to {topic}",
            "Improve existing methods for {topic}"
        ])
        
        for phrase in key_phrases[:5]:
            for template in templates:
                idea = {
                    'title': template.format(topic=phrase),
                    'description': f"Focus on {phrase} to create positive impact in {domain}",
                    'domain': domain,
                    'confidence': 0.65,
                    'source': 'domain_specific',
                    'key_phrases': [phrase]
                }
                ideas.append(idea)
        
        return ideas
    
    def extract_ideas_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract ideas from text using NLTK only."""
        try:
            # Classify domain
            domain = self._classify_domain(text)
            
            # Generate ideas
            ideas = self._generate_ideas_from_text(text, domain)
            
            # Remove duplicates and limit results
            unique_ideas = []
            seen_titles = set()
            
            for idea in ideas:
                if idea['title'] not in seen_titles:
                    unique_ideas.append(idea)
                    seen_titles.add(idea['title'])
            
            return unique_ideas[:20]  # Limit to 20 ideas
            
        except Exception as e:
            logger.error(f"Error extracting ideas: {e}")
            return []

# Create a fallback function for the hybrid extractor
def create_nltk_fallback():
    """Create an NLTK-only fallback for when spaCy is not available."""
    return NLTKIdeaExtractor()
