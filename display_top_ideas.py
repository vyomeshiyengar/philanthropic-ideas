#!/usr/bin/env python3
"""
Script to display top evaluated ideas and evaluate remaining ideas.
"""
import logging
from sqlalchemy.orm import Session
from sqlalchemy import desc
from storage.database import db_manager
from storage.models import ExtractedIdea, IdeaEvaluation
from scoring.idea_evaluator import IdeaEvaluator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def display_top_ideas(limit=10):
    """Display the top evaluated ideas."""
    session = Session(db_manager.engine)
    
    try:
        # Get top evaluated ideas with their details
        top_evaluations = session.query(IdeaEvaluation, ExtractedIdea).join(
            ExtractedIdea, IdeaEvaluation.idea_id == ExtractedIdea.id
        ).order_by(desc(IdeaEvaluation.overall_score)).limit(limit).all()
        
        print(f"\n🏆 TOP {len(top_evaluations)} EVALUATED IDEAS")
        print("=" * 80)
        
        for i, (evaluation, idea) in enumerate(top_evaluations, 1):
            print(f"\n{i}. {idea.title}")
            print(f"   Score: {evaluation.overall_score:.2f}/10")
            print(f"   Domain: {idea.domain}")
            print(f"   Type: {idea.idea_type}")
            print(f"   Description: {idea.description[:200]}...")
            print(f"   Impact: {evaluation.impact_score:.2f}, Neglectedness: {evaluation.neglectedness_score:.2f}")
            print(f"   Tractability: {evaluation.tractability_score:.2f}, Scalability: {evaluation.scalability_score:.2f}")
            if hasattr(evaluation, 'scoring_explanation') and evaluation.scoring_explanation:
                print(f"   Reasoning: {evaluation.scoring_explanation[:150]}...")
            print("-" * 80)
            
    finally:
        session.close()

def get_evaluation_stats():
    """Get statistics about idea evaluations."""
    session = Session(db_manager.engine)
    
    try:
        total_ideas = session.query(ExtractedIdea).count()
        evaluated_ideas = session.query(IdeaEvaluation).count()
        # Count unique evaluated idea IDs
        evaluated_idea_ids = session.query(IdeaEvaluation.idea_id).distinct().count()
        unevaluated_ideas = total_ideas - evaluated_idea_ids
        
        print(f"\n📊 EVALUATION STATISTICS")
        print("=" * 40)
        print(f"Total ideas: {total_ideas}")
        print(f"Total evaluations: {evaluated_ideas}")
        print(f"Unique evaluated ideas: {evaluated_idea_ids}")
        print(f"Unevaluated ideas: {unevaluated_ideas}")
        
        if evaluated_ideas > 0:
            from sqlalchemy import func
            avg_score = session.query(func.avg(IdeaEvaluation.overall_score)).scalar()
            if avg_score:
                print(f"Average score: {avg_score:.2f}/10")
        
        return total_ideas, evaluated_ideas, unevaluated_ideas
        
    finally:
        session.close()

def evaluate_remaining_ideas():
    """Evaluate ideas that haven't been evaluated yet."""
    session = Session(db_manager.engine)
    
    try:
        # Get unevaluated ideas
        evaluated_idea_ids = session.query(IdeaEvaluation.idea_id).distinct()
        unevaluated_ideas = session.query(ExtractedIdea).filter(
            ~ExtractedIdea.id.in_(evaluated_idea_ids)
        ).all()
        
        if not unevaluated_ideas:
            print("\n✅ All ideas have been evaluated!")
            return
        
        print(f"\n🔄 EVALUATING {len(unevaluated_ideas)} REMAINING IDEAS")
        print("=" * 50)
        
        # Initialize evaluator
        evaluator = IdeaEvaluator()
        
        # Evaluate ideas in batches
        batch_size = 50
        for i in range(0, len(unevaluated_ideas), batch_size):
            batch = unevaluated_ideas[i:i + batch_size]
            print(f"\nProcessing batch {i//batch_size + 1}/{(len(unevaluated_ideas) + batch_size - 1)//batch_size}")
            
            for idea in batch:
                try:
                    # Create evaluation
                    evaluation = evaluator.evaluate_idea(idea)
                    
                    # Save to database
                    db_evaluation = IdeaEvaluation(
                        idea_id=idea.id,
                        impact_score=evaluation['impact_score'],
                        impact_confidence=evaluation.get('impact_confidence'),
                        impact_notes=evaluation.get('impact_notes'),
                        neglectedness_score=evaluation['neglectedness_score'],
                        annual_funding_estimate=evaluation.get('annual_funding_estimate'),
                        neglectedness_notes=evaluation.get('neglectedness_notes'),
                        tractability_score=evaluation['tractability_score'],
                        tractability_notes=evaluation.get('tractability_notes'),
                        scalability_score=evaluation['scalability_score'],
                        scalability_notes=evaluation.get('scalability_notes'),
                        overall_score=evaluation['overall_score'],
                        benchmark_comparison=evaluation.get('benchmark_comparison'),
                        evaluator='automated',
                        evaluation_method='automated',
                        scoring_explanation=evaluation.get('scoring_explanation')
                    )
                    
                    session.add(db_evaluation)
                    print(f"  ✅ Evaluated: {idea.title[:50]}... (Score: {evaluation['overall_score']:.2f})")
                    
                except Exception as e:
                    print(f"  ❌ Failed to evaluate: {idea.title[:50]}... - {e}")
                    continue
            
            # Commit batch
            session.commit()
            print(f"  💾 Committed batch {i//batch_size + 1}")
        
        print(f"\n🎉 Completed evaluation of {len(unevaluated_ideas)} ideas!")
        
    except Exception as e:
        print(f"❌ Error during evaluation: {e}")
        session.rollback()
    finally:
        session.close()

def main():
    """Main function to display top ideas and evaluate remaining ones."""
    print("🚀 PHILANTHROPIC IDEAS DISPLAY & EVALUATION")
    print("=" * 60)
    
    # Display current statistics
    total, evaluated, unevaluated = get_evaluation_stats()
    
    # Display top ideas
    display_top_ideas(limit=10)
    
    # Ask if user wants to evaluate remaining ideas
    if unevaluated > 0:
        response = input(f"\n🤔 Would you like to evaluate the remaining {unevaluated} ideas? (y/n): ")
        if response.lower() in ['y', 'yes']:
            evaluate_remaining_ideas()
            
            # Display updated top ideas
            print("\n" + "="*60)
            print("🔄 UPDATED TOP IDEAS AFTER EVALUATION")
            display_top_ideas(limit=10)
        else:
            print("\n⏸️  Skipping evaluation of remaining ideas.")
    else:
        print("\n✅ All ideas have been evaluated!")

if __name__ == "__main__":
    main()
