"""
Idea evaluation module for scoring philanthropic opportunities.
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json

from storage.database import db_manager
from storage.models import ExtractedIdea, IdeaEvaluation, BenchmarkIntervention
from config.settings import settings

logger = logging.getLogger(__name__)


class IdeaEvaluator:
    """Evaluates philanthropic ideas based on multiple criteria."""
    
    def __init__(self):
        self.benchmarks = {}
        self._load_benchmarks()
    
    def _load_benchmarks(self):
        """Load benchmark interventions from settings."""
        self.benchmarks = settings.BENCHMARKS.copy()
        
        # Also load from database if available
        try:
            with db_manager.get_session() as session:
                db_benchmarks = session.query(BenchmarkIntervention).all()
                for benchmark in db_benchmarks:
                    self.benchmarks[benchmark.primary_metric] = {
                        "name": benchmark.name,
                        "url": benchmark.url,
                        "cost_per_unit": benchmark.cost_per_unit,
                        "description": benchmark.description,
                        "effectiveness_estimate": benchmark.effectiveness_estimate,
                        "evidence_quality": benchmark.evidence_quality
                    }
        except Exception as e:
            logger.warning(f"Failed to load benchmarks from database: {e}")
    
    def evaluate_idea(self, idea_id: int, evaluator: str = "automated") -> Optional[Dict[str, Any]]:
        """Evaluate a single idea and save the evaluation."""
        try:
            with db_manager.get_session() as session:
                idea = session.query(ExtractedIdea).filter(ExtractedIdea.id == idea_id).first()
                
                if not idea:
                    logger.error(f"Idea {idea_id} not found")
                    return None
                
                # Perform evaluation
                evaluation = self._perform_evaluation(idea)
                
                # Save evaluation to database
                idea_evaluation = IdeaEvaluation(
                    idea_id=idea_id,
                    impact_score=evaluation["impact_score"],
                    impact_confidence=evaluation["impact_confidence"],
                    impact_notes=evaluation["impact_notes"],
                    neglectedness_score=evaluation["neglectedness_score"],
                    annual_funding_estimate=evaluation["annual_funding_estimate"],
                    neglectedness_notes=evaluation["neglectedness_notes"],
                    tractability_score=evaluation["tractability_score"],
                    tractability_notes=evaluation["tractability_notes"],
                    scalability_score=evaluation["scalability_score"],
                    scalability_notes=evaluation["scalability_notes"],
                    overall_score=evaluation["overall_score"],
                    benchmark_comparison=evaluation["benchmark_comparison"],
                    evaluator=evaluator,
                    evaluation_method="automated"
                )
                
                session.add(idea_evaluation)
                session.commit()
                session.refresh(idea_evaluation)
                
                logger.info(f"Evaluated idea {idea_id}: overall score {evaluation['overall_score']:.2f}")
                
                return {
                    "evaluation_id": idea_evaluation.id,
                    "idea_id": idea_id,
                    "overall_score": evaluation["overall_score"],
                    "scores": {
                        "impact": evaluation["impact_score"],
                        "neglectedness": evaluation["neglectedness_score"],
                        "tractability": evaluation["tractability_score"],
                        "scalability": evaluation["scalability_score"]
                    },
                    "benchmark_comparison": evaluation["benchmark_comparison"]
                }
                
        except Exception as e:
            logger.error(f"Failed to evaluate idea {idea_id}: {e}")
            return None
    
    def _perform_evaluation(self, idea: ExtractedIdea) -> Dict[str, Any]:
        """Perform the actual evaluation of an idea."""
        # Impact evaluation
        impact_score, impact_confidence, impact_notes = self._evaluate_impact(idea)
        
        # Neglectedness evaluation
        neglectedness_score, annual_funding, neglectedness_notes = self._evaluate_neglectedness(idea)
        
        # Tractability evaluation
        tractability_score, tractability_notes = self._evaluate_tractability(idea)
        
        # Scalability evaluation
        scalability_score, scalability_notes = self._evaluate_scalability(idea)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(
            impact_score, neglectedness_score, tractability_score, scalability_score
        )
        
        # Benchmark comparison
        benchmark_comparison = self._compare_to_benchmark(idea, impact_score)
        
        return {
            "impact_score": impact_score,
            "impact_confidence": impact_confidence,
            "impact_notes": impact_notes,
            "neglectedness_score": neglectedness_score,
            "annual_funding_estimate": annual_funding,
            "neglectedness_notes": neglectedness_notes,
            "tractability_score": tractability_score,
            "tractability_notes": tractability_notes,
            "scalability_score": scalability_score,
            "scalability_notes": scalability_notes,
            "overall_score": overall_score,
            "benchmark_comparison": benchmark_comparison
        }
    
    def _evaluate_impact(self, idea: ExtractedIdea) -> Tuple[float, float, str]:
        """Evaluate the potential impact of an idea."""
        base_score = 5.0  # Neutral starting point
        confidence = 0.5  # Medium confidence
        
        # Domain-specific impact adjustments
        domain_impact_factors = {
            "health": 1.2,  # Health interventions often have high impact
            "education": 1.1,  # Education has long-term benefits
            "economic_development": 1.0,  # Standard impact
            "animal_welfare": 0.8,  # Lower priority than human welfare
            "climate": 1.3,  # High global impact
            "wellbeing": 1.0  # Standard impact
        }
        
        domain_factor = domain_impact_factors.get(idea.domain, 1.0)
        base_score *= domain_factor
        
        # Idea type adjustments
        if idea.idea_type == "newly_viable":
            base_score += 1.0  # New opportunities might have higher impact
        elif idea.idea_type == "evergreen":
            base_score += 0.5  # Evergreen ideas are proven but might be saturated
        
        # Confidence score from extraction
        if idea.confidence_score:
            confidence = idea.confidence_score
        
        # Generate impact notes
        impact_notes = f"Domain: {idea.domain}, Type: {idea.idea_type}, "
        impact_notes += f"Confidence: {confidence:.2f}, Domain factor: {domain_factor}"
        
        return min(base_score, 10.0), confidence, impact_notes
    
    def _evaluate_neglectedness(self, idea: ExtractedIdea) -> Tuple[float, Optional[float], str]:
        """Evaluate how neglected the area is."""
        base_score = 5.0
        annual_funding = None
        
        # Domain-specific neglectedness
        domain_neglectedness = {
            "health": 3.0,  # Well-funded
            "education": 4.0,  # Moderately funded
            "economic_development": 4.5,  # Somewhat funded
            "animal_welfare": 8.0,  # Highly neglected ($200M/year total)
            "climate": 2.0,  # Very well funded
            "wellbeing": 6.0  # Moderately neglected
        }
        
        base_score = domain_neglectedness.get(idea.domain, 5.0)
        
        # Estimate annual funding based on domain
        domain_funding_estimates = {
            "health": 10000000000,  # $10B
            "education": 5000000000,  # $5B
            "economic_development": 3000000000,  # $3B
            "animal_welfare": 200000000,  # $200M
            "climate": 50000000000,  # $50B
            "wellbeing": 1000000000  # $1B
        }
        
        annual_funding = domain_funding_estimates.get(idea.domain)
        
        # Adjust based on idea type
        if idea.idea_type == "evergreen":
            base_score += 1.0  # Evergreen ideas are often more neglected
        
        # Generate neglectedness notes
        neglectedness_notes = f"Domain: {idea.domain}, Estimated annual funding: ${annual_funding:,}"
        if annual_funding:
            if annual_funding < 1000000000:  # < $1B
                neglectedness_notes += " (Highly neglected)"
            elif annual_funding < 5000000000:  # < $5B
                neglectedness_notes += " (Moderately neglected)"
            else:
                neglectedness_notes += " (Well funded)"
        
        return min(base_score, 10.0), annual_funding, neglectedness_notes
    
    def _evaluate_tractability(self, idea: ExtractedIdea) -> Tuple[float, str]:
        """Evaluate how tractable the idea is to implement."""
        base_score = 5.0
        
        # Domain-specific tractability
        domain_tractability = {
            "health": 7.0,  # Health interventions are often well-understood
            "education": 6.0,  # Education interventions can be complex
            "economic_development": 5.0,  # Mixed tractability
            "animal_welfare": 8.0,  # Often straightforward interventions
            "climate": 4.0,  # Complex global coordination required
            "wellbeing": 6.0  # Mental health interventions can be complex
        }
        
        base_score = domain_tractability.get(idea.domain, 5.0)
        
        # Adjust based on idea type
        if idea.idea_type == "evergreen":
            base_score += 1.0  # Evergreen ideas are often more tractable
        elif idea.idea_type == "newly_viable":
            base_score -= 0.5  # New ideas might be less tractable
        
        # Generate tractability notes
        tractability_notes = f"Domain: {idea.domain}, Type: {idea.idea_type}"
        
        return min(base_score, 10.0), tractability_notes
    
    def _evaluate_scalability(self, idea: ExtractedIdea) -> Tuple[float, str]:
        """Evaluate how scalable the idea is."""
        base_score = 5.0
        
        # Domain-specific scalability
        domain_scalability = {
            "health": 8.0,  # Health interventions can scale globally
            "education": 7.0,  # Education can scale but requires infrastructure
            "economic_development": 6.0,  # Can scale but context-dependent
            "animal_welfare": 9.0,  # Can scale globally (e.g., corporate campaigns)
            "climate": 9.0,  # Global impact potential
            "wellbeing": 6.0  # Can scale but requires individual attention
        }
        
        base_score = domain_scalability.get(idea.domain, 5.0)
        
        # Adjust based on idea type
        if idea.idea_type == "newly_viable":
            base_score += 0.5  # New ideas might have better scalability potential
        
        # Generate scalability notes
        scalability_notes = f"Domain: {idea.domain}, Type: {idea.idea_type}"
        
        return min(base_score, 10.0), scalability_notes
    
    def _calculate_overall_score(self, impact: float, neglectedness: float, 
                               tractability: float, scalability: float) -> float:
        """Calculate the overall score using weighted criteria."""
        weights = settings.SCORING_WEIGHTS
        
        overall_score = (
            impact * weights["impact"] +
            neglectedness * weights["neglectedness"] +
            tractability * weights["tractability"] +
            scalability * weights["scalability"]
        )
        
        return min(overall_score, 10.0)
    
    def _compare_to_benchmark(self, idea: ExtractedIdea, impact_score: float) -> Dict[str, Any]:
        """Compare the idea to benchmark interventions."""
        benchmark = self.benchmarks.get(idea.primary_metric)
        
        if not benchmark:
            return {"benchmark_available": False}
        
        # Calculate relative effectiveness
        benchmark_cost_per_unit = benchmark.get("cost_per_unit", 100)
        
        # Estimate cost-effectiveness (lower is better)
        estimated_cost_per_unit = benchmark_cost_per_unit * (10.0 / impact_score)
        
        comparison = {
            "benchmark_available": True,
            "benchmark_name": benchmark.get("name", "Unknown"),
            "benchmark_url": benchmark.get("url", ""),
            "benchmark_cost_per_unit": benchmark_cost_per_unit,
            "estimated_cost_per_unit": estimated_cost_per_unit,
            "relative_effectiveness": impact_score / 10.0,  # Normalized to 0-1
            "cost_effectiveness_ratio": estimated_cost_per_unit / benchmark_cost_per_unit
        }
        
        return comparison
    
    def evaluate_all_ideas(self, domain: Optional[str] = None, 
                          evaluator: str = "automated") -> Dict[str, Any]:
        """Evaluate all ideas in the database."""
        try:
            with db_manager.get_session() as session:
                # Query ideas
                query = session.query(ExtractedIdea)
                
                if domain:
                    query = query.filter(ExtractedIdea.domain == domain)
                
                ideas = query.all()
                
                results = {
                    "total_ideas": len(ideas),
                    "evaluated": 0,
                    "failed": 0,
                    "evaluations": []
                }
                
                for idea in ideas:
                    try:
                        evaluation = self.evaluate_idea(idea.id, evaluator)
                        if evaluation:
                            results["evaluated"] += 1
                            results["evaluations"].append(evaluation)
                        else:
                            results["failed"] += 1
                    except Exception as e:
                        logger.error(f"Failed to evaluate idea {idea.id}: {e}")
                        results["failed"] += 1
                
                logger.info(f"Evaluated {results['evaluated']} ideas, {results['failed']} failed")
                return results
                
        except Exception as e:
            logger.error(f"Failed to evaluate all ideas: {e}")
            return {"error": str(e)}
    
    def get_top_ideas(self, domain: Optional[str] = None, metric: Optional[str] = None,
                     limit: int = 10) -> List[Dict[str, Any]]:
        """Get the top-scoring ideas."""
        try:
            with db_manager.get_session() as session:
                # Query ideas with their latest evaluation
                query = session.query(ExtractedIdea, IdeaEvaluation).join(
                    IdeaEvaluation, ExtractedIdea.id == IdeaEvaluation.idea_id
                )
                
                if domain:
                    query = query.filter(ExtractedIdea.domain == domain)
                
                if metric:
                    query = query.filter(ExtractedIdea.primary_metric == metric)
                
                # Get the latest evaluation for each idea
                results = []
                for idea, evaluation in query.order_by(IdeaEvaluation.overall_score.desc()).limit(limit):
                    results.append({
                        "idea_id": idea.id,
                        "title": idea.title,
                        "description": idea.description,
                        "domain": idea.domain,
                        "primary_metric": idea.primary_metric,
                        "idea_type": idea.idea_type,
                        "overall_score": evaluation.overall_score,
                        "impact_score": evaluation.impact_score,
                        "neglectedness_score": evaluation.neglectedness_score,
                        "tractability_score": evaluation.tractability_score,
                        "scalability_score": evaluation.scalability_score,
                        "benchmark_comparison": evaluation.benchmark_comparison
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Failed to get top ideas: {e}")
            return []
    
    def generate_contrarian_ranking(self, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        """Generate a contrarian ranking that challenges conventional wisdom."""
        try:
            with db_manager.get_session() as session:
                # Get all evaluated ideas
                query = session.query(ExtractedIdea, IdeaEvaluation).join(
                    IdeaEvaluation, ExtractedIdea.id == IdeaEvaluation.idea_id
                )
                
                if domain:
                    query = query.filter(ExtractedIdea.domain == domain)
                
                ideas_with_evaluations = query.all()
                
                # Apply contrarian adjustments
                contrarian_ideas = []
                for idea, evaluation in ideas_with_evaluations:
                    contrarian_score = self._calculate_contrarian_score(idea, evaluation)
                    
                    contrarian_ideas.append({
                        "idea_id": idea.id,
                        "title": idea.title,
                        "description": idea.description,
                        "domain": idea.domain,
                        "primary_metric": idea.primary_metric,
                        "idea_type": idea.idea_type,
                        "original_score": evaluation.overall_score,
                        "contrarian_score": contrarian_score,
                        "contrarian_reasoning": self._generate_contrarian_reasoning(idea, evaluation)
                    })
                
                # Sort by contrarian score
                contrarian_ideas.sort(key=lambda x: x["contrarian_score"], reverse=True)
                
                return contrarian_ideas
                
        except Exception as e:
            logger.error(f"Failed to generate contrarian ranking: {e}")
            return []
    
    def _calculate_contrarian_score(self, idea: ExtractedIdea, evaluation: IdeaEvaluation) -> float:
        """Calculate a contrarian score that challenges conventional wisdom."""
        base_score = evaluation.overall_score
        
        # Boost neglected areas
        if evaluation.neglectedness_score > 7.0:
            base_score += 1.0
        
        # Boost newly viable ideas (they might be overlooked)
        if idea.idea_type == "newly_viable":
            base_score += 0.5
        
        # Boost areas with low funding
        if evaluation.annual_funding_estimate and evaluation.annual_funding_estimate < 1000000000:
            base_score += 0.5
        
        # Boost ideas that might have long-term effects
        if idea.domain in ["education", "economic_development", "climate"]:
            base_score += 0.3
        
        return min(base_score, 10.0)
    
    def _generate_contrarian_reasoning(self, idea: ExtractedIdea, evaluation: IdeaEvaluation) -> str:
        """Generate reasoning for why this idea might be undervalued."""
        reasoning = []
        
        if evaluation.neglectedness_score > 7.0:
            reasoning.append("Highly neglected area with low funding")
        
        if idea.idea_type == "newly_viable":
            reasoning.append("Newly viable opportunity that might be overlooked")
        
        if evaluation.annual_funding_estimate and evaluation.annual_funding_estimate < 1000000000:
            reasoning.append("Low funding suggests potential for high marginal impact")
        
        if idea.domain in ["education", "economic_development"]:
            reasoning.append("Long-term effects might be underestimated")
        
        if not reasoning:
            reasoning.append("Standard evaluation")
        
        return "; ".join(reasoning)
