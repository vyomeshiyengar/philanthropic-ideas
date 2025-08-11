"""
Idea extraction module for identifying philanthropic opportunities from raw data.
"""
import logging
import re
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from textblob import TextBlob
import spacy

from storage.database import db_manager
from storage.models import RawData, ExtractedIdea
from config.settings import settings

logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')


class IdeaExtractor:
    """Extracts philanthropic ideas from raw data using NLP techniques."""
    
    def __init__(self):
        self.nlp = None
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        self._initialize_nlp()
        
        # Keywords that indicate opportunities
        self.opportunity_keywords = {
            "health": [
                "intervention", "treatment", "prevention", "vaccine", "therapy",
                "clinical trial", "effectiveness", "impact", "outcome", "improvement",
                "reduction", "decrease", "increase", "better", "successful"
            ],
            "education": [
                "learning", "teaching", "pedagogy", "curriculum", "instruction",
                "student", "achievement", "performance", "improvement", "effectiveness",
                "intervention", "program", "initiative", "success", "outcome"
            ],
            "economic_development": [
                "poverty", "income", "employment", "job", "entrepreneurship",
                "microfinance", "development", "growth", "improvement", "increase",
                "reduction", "program", "intervention", "effectiveness", "impact"
            ],
            "animal_welfare": [
                "animal", "welfare", "suffering", "livestock", "farming",
                "cruelty", "protection", "rights", "improvement", "reduction",
                "intervention", "program", "effectiveness", "impact", "better"
            ],
            "climate": [
                "climate", "carbon", "emission", "reduction", "mitigation",
                "adaptation", "sustainability", "renewable", "energy", "technology",
                "intervention", "program", "effectiveness", "impact", "improvement"
            ],
            "wellbeing": [
                "wellbeing", "happiness", "mental health", "depression", "anxiety",
                "satisfaction", "quality of life", "improvement", "intervention",
                "therapy", "treatment", "effectiveness", "impact", "better"
            ]
        }
        
        # Phrases that indicate newly viable opportunities
        self.newly_viable_phrases = [
            "recent advances", "new technology", "breakthrough", "innovation",
            "emerging", "novel approach", "cutting edge", "state of the art",
            "recently developed", "newly available", "recent discovery",
            "technological breakthrough", "scientific breakthrough"
        ]
        
        # Phrases that indicate evergreen opportunities
        self.evergreen_phrases = [
            "long-standing", "persistent", "ongoing", "chronic", "enduring",
            "neglected", "overlooked", "underfunded", "understudied",
            "obvious solution", "simple intervention", "low-hanging fruit",
            "known problem", "well-established", "proven approach"
        ]
    
    def _initialize_nlp(self):
        """Initialize spaCy NLP model."""
        try:
            # Try to load English model, download if not available
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy English model not found. Installing...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
    
    def extract_ideas_from_raw_data(self, raw_data_id: Optional[int] = None, 
                                  domain: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract ideas from raw data in the database."""
        try:
            with db_manager.get_session() as session:
                # Query raw data
                query = session.query(RawData)
                
                if raw_data_id:
                    query = query.filter(RawData.id == raw_data_id)
                
                if domain:
                    # Filter by domain using metadata
                    query = query.filter(RawData.metadata.contains({"domain": domain}))
                
                raw_data_items = query.all()
                
                extracted_ideas = []
                
                for item in raw_data_items:
                    ideas = self._extract_ideas_from_item(item)
                    extracted_ideas.extend(ideas)
                
                logger.info(f"Extracted {len(extracted_ideas)} ideas from {len(raw_data_items)} raw data items")
                return extracted_ideas
                
        except Exception as e:
            logger.error(f"Failed to extract ideas from raw data: {e}")
            return []
    
    def _extract_ideas_from_item(self, raw_data: RawData) -> List[Dict[str, Any]]:
        """Extract ideas from a single raw data item."""
        ideas = []
        
        try:
            # Combine title and abstract for analysis
            text_content = ""
            if raw_data.title:
                text_content += raw_data.title + ". "
            if raw_data.abstract:
                text_content += raw_data.abstract
            
            if not text_content.strip():
                return ideas
            
            # Analyze the text
            doc = self.nlp(text_content)
            
            # Extract sentences that might contain ideas
            sentences = sent_tokenize(text_content)
            
            for sentence in sentences:
                idea = self._extract_idea_from_sentence(sentence, raw_data)
                if idea:
                    ideas.append(idea)
            
            # Also analyze the full text if available
            if raw_data.full_text and len(raw_data.full_text) > len(text_content):
                full_text_ideas = self._extract_ideas_from_full_text(raw_data.full_text, raw_data)
                ideas.extend(full_text_ideas)
            
            return ideas
            
        except Exception as e:
            logger.error(f"Failed to extract ideas from item {raw_data.id}: {e}")
            return []
    
    def _extract_idea_from_sentence(self, sentence: str, raw_data: RawData) -> Optional[Dict[str, Any]]:
        """Extract a single idea from a sentence."""
        try:
            # Clean and normalize the sentence
            sentence = sentence.strip()
            if len(sentence) < 20:  # Too short to be meaningful
                return None
            
            # Analyze the sentence
            doc = self.nlp(sentence)
            
            # Determine domain
            domain = self._classify_domain(sentence, doc)
            if not domain:
                return None
            
            # Determine primary metric
            primary_metric = self._classify_primary_metric(sentence, domain)
            
            # Determine idea type
            idea_type = self._classify_idea_type(sentence)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence(sentence, domain, idea_type)
            
            # Only return ideas with sufficient confidence
            if confidence_score < 0.3:
                return None
            
            # Generate idea title and description
            title = self._generate_idea_title(sentence, domain)
            description = self._generate_idea_description(sentence, domain)
            
            return {
                "raw_data_id": raw_data.id,
                "title": title,
                "description": description,
                "domain": domain,
                "primary_metric": primary_metric,
                "idea_type": idea_type,
                "confidence_score": confidence_score,
                "extraction_method": "nlp",
                "source_sentence": sentence,
                "source_title": raw_data.title,
                "source_authors": raw_data.authors,
                "source_url": raw_data.url
            }
            
        except Exception as e:
            logger.error(f"Failed to extract idea from sentence: {e}")
            return None
    
    def _classify_domain(self, sentence: str, doc) -> Optional[str]:
        """Classify the domain of the sentence."""
        sentence_lower = sentence.lower()
        
        # Count domain-specific keywords
        domain_scores = {}
        
        for domain, keywords in self.opportunity_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in sentence_lower:
                    score += 1
            
            if score > 0:
                domain_scores[domain] = score
        
        # Return the domain with the highest score
        if domain_scores:
            return max(domain_scores, key=domain_scores.get)
        
        return None
    
    def _classify_primary_metric(self, sentence: str, domain: str) -> str:
        """Classify the primary metric for the idea."""
        sentence_lower = sentence.lower()
        
        metric_mapping = {
            "health": "dalys",
            "education": "log_income",  # Education often correlates with income
            "economic_development": "log_income",
            "animal_welfare": "walys",
            "climate": "co2",
            "wellbeing": "welbys"
        }
        
        # Default mapping
        primary_metric = metric_mapping.get(domain, "welbys")
        
        # Override based on specific keywords in the sentence
        if "daly" in sentence_lower or "disability-adjusted" in sentence_lower:
            primary_metric = "dalys"
        elif "waly" in sentence_lower or "welfare-adjusted" in sentence_lower:
            primary_metric = "walys"
        elif "welby" in sentence_lower or "wellbeing-adjusted" in sentence_lower:
            primary_metric = "welbys"
        elif "co2" in sentence_lower or "carbon" in sentence_lower:
            primary_metric = "co2"
        elif "income" in sentence_lower or "gdp" in sentence_lower:
            primary_metric = "log_income"
        
        return primary_metric
    
    def _classify_idea_type(self, sentence: str) -> str:
        """Classify whether this is a newly viable or evergreen idea."""
        sentence_lower = sentence.lower()
        
        # Check for newly viable indicators
        newly_viable_score = 0
        for phrase in self.newly_viable_phrases:
            if phrase.lower() in sentence_lower:
                newly_viable_score += 1
        
        # Check for evergreen indicators
        evergreen_score = 0
        for phrase in self.evergreen_phrases:
            if phrase.lower() in sentence_lower:
                evergreen_score += 1
        
        # Determine type based on scores
        if newly_viable_score > evergreen_score:
            return "newly_viable"
        elif evergreen_score > newly_viable_score:
            return "evergreen"
        else:
            # Default to newly viable if unclear
            return "newly_viable"
    
    def _calculate_confidence(self, sentence: str, domain: str, idea_type: str) -> float:
        """Calculate confidence score for the extracted idea."""
        confidence = 0.0
        
        # Base confidence
        if domain and idea_type:
            confidence += 0.2
        
        # Length factor (longer sentences tend to be more informative)
        sentence_length = len(sentence.split())
        if 10 <= sentence_length <= 50:
            confidence += 0.2
        elif sentence_length > 50:
            confidence += 0.1
        
        # Keyword density
        domain_keywords = self.opportunity_keywords.get(domain, [])
        keyword_count = sum(1 for keyword in domain_keywords 
                          if keyword.lower() in sentence.lower())
        confidence += min(keyword_count * 0.1, 0.3)
        
        # Sentiment analysis (positive sentiment might indicate opportunities)
        try:
            blob = TextBlob(sentence)
            sentiment = blob.sentiment.polarity
            if sentiment > 0:
                confidence += 0.1
        except:
            pass
        
        # Presence of specific opportunity indicators
        opportunity_indicators = [
            "intervention", "program", "initiative", "approach", "method",
            "strategy", "solution", "treatment", "therapy", "prevention"
        ]
        
        indicator_count = sum(1 for indicator in opportunity_indicators 
                            if indicator.lower() in sentence.lower())
        confidence += min(indicator_count * 0.05, 0.2)
        
        return min(confidence, 1.0)
    
    def _generate_idea_title(self, sentence: str, domain: str) -> str:
        """Generate a concise title for the idea."""
        # Extract key phrases from the sentence
        doc = self.nlp(sentence)
        
        # Look for noun phrases
        noun_phrases = [chunk.text for chunk in doc.noun_chunks]
        
        if noun_phrases:
            # Use the first significant noun phrase
            for phrase in noun_phrases:
                if len(phrase.split()) >= 2 and len(phrase) < 50:
                    return f"{phrase.title()} for {domain.replace('_', ' ').title()}"
        
        # Fallback: use first few words
        words = sentence.split()[:6]
        title = " ".join(words).title()
        if len(title) > 60:
            title = title[:57] + "..."
        
        return title
    
    def _generate_idea_description(self, sentence: str, domain: str) -> str:
        """Generate a description for the idea."""
        # Clean up the sentence
        description = sentence.strip()
        
        # Remove extra whitespace
        description = re.sub(r'\s+', ' ', description)
        
        # Truncate if too long
        if len(description) > 500:
            description = description[:497] + "..."
        
        return description
    
    def _extract_ideas_from_full_text(self, full_text: str, raw_data: RawData) -> List[Dict[str, Any]]:
        """Extract ideas from full text content."""
        ideas = []
        
        try:
            # Split into paragraphs
            paragraphs = full_text.split('\n\n')
            
            for paragraph in paragraphs:
                if len(paragraph.strip()) < 50:  # Skip very short paragraphs
                    continue
                
                # Extract ideas from each paragraph
                paragraph_ideas = self._extract_ideas_from_paragraph(paragraph, raw_data)
                ideas.extend(paragraph_ideas)
            
            return ideas
            
        except Exception as e:
            logger.error(f"Failed to extract ideas from full text: {e}")
            return []
    
    def _extract_ideas_from_paragraph(self, paragraph: str, raw_data: RawData) -> List[Dict[str, Any]]:
        """Extract ideas from a paragraph."""
        ideas = []
        
        try:
            # Split into sentences
            sentences = sent_tokenize(paragraph)
            
            for sentence in sentences:
                idea = self._extract_idea_from_sentence(sentence, raw_data)
                if idea:
                    ideas.append(idea)
            
            return ideas
            
        except Exception as e:
            logger.error(f"Failed to extract ideas from paragraph: {e}")
            return []
    
    def save_extracted_ideas(self, ideas: List[Dict[str, Any]]) -> int:
        """Save extracted ideas to the database."""
        saved_count = 0
        
        try:
            with db_manager.get_session() as session:
                for idea_data in ideas:
                    try:
                        # Check if idea already exists (basic deduplication)
                        existing = session.query(ExtractedIdea).filter(
                            ExtractedIdea.raw_data_id == idea_data["raw_data_id"],
                            ExtractedIdea.title == idea_data["title"]
                        ).first()
                        
                        if existing:
                            continue
                        
                        # Create new idea
                        idea = ExtractedIdea(
                            raw_data_id=idea_data["raw_data_id"],
                            title=idea_data["title"],
                            description=idea_data["description"],
                            domain=idea_data["domain"],
                            primary_metric=idea_data["primary_metric"],
                            idea_type=idea_data["idea_type"],
                            confidence_score=idea_data["confidence_score"],
                            extraction_method=idea_data["extraction_method"]
                        )
                        
                        session.add(idea)
                        saved_count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to save idea: {e}")
                        continue
                
                session.commit()
                logger.info(f"Saved {saved_count} new ideas to database")
                
        except Exception as e:
            logger.error(f"Failed to save extracted ideas: {e}")
        
        return saved_count
