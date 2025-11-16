"""
Quality Loop Agent
Evaluates and iteratively improves research brief quality
Implements loop until quality score ≥ 90% or max 3 iterations
"""

from google import genai
from google.genai import types
import logging
from typing import Dict, Any
import json

from src.schemas import ResearchBrief, QualityScore
from src.memory import memory_bank

logger = logging.getLogger(__name__)


class QualityLoopAgent:
    """
    Agent that evaluates quality and iteratively improves research brief
    Uses ADK's loop agent pattern
    """

    def __init__(self, client: genai.Client):
        """
        Initialize Quality Loop Agent

        Args:
            client: Google GenAI client instance
        """
        self.client = client
        self.model_id = "gemini-2.0-flash-exp"
        self.max_iterations = 3
        self.target_score = 90
        logger.info("QualityLoopAgent initialized")

    def evaluate_and_improve(self, brief: ResearchBrief) -> ResearchBrief:
        """
        Evaluate brief and iteratively improve until quality threshold met

        Args:
            brief: Initial ResearchBrief

        Returns:
            Improved ResearchBrief
        """
        logger.info("Starting quality improvement loop")

        current_brief = brief
        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"Quality loop iteration {iteration}/{self.max_iterations}")

            # Evaluate current brief
            quality_score = self.evaluate_quality(current_brief)

            # Store iteration in memory
            memory_bank.add_iteration({
                "iteration": iteration,
                "quality_score": quality_score.overall_score,
                "clarity": quality_score.clarity_score,
                "correctness": quality_score.correctness_score,
                "completeness": quality_score.completeness_score,
                "feedback": quality_score.feedback
            })

            logger.info(f"Quality score: {quality_score.overall_score}/100")

            # Check if target met
            if quality_score.overall_score >= self.target_score:
                logger.info(f"Target quality reached: {quality_score.overall_score}/100")
                break

            # If not last iteration and needs improvement, improve brief
            if iteration < self.max_iterations and quality_score.needs_revision:
                logger.info("Improving brief based on feedback...")
                current_brief = self.improve_brief(current_brief, quality_score)
            else:
                logger.info("Max iterations reached or no improvement needed")
                break

        logger.info(f"Quality loop completed after {iteration} iterations")
        return current_brief

    def evaluate_quality(self, brief: ResearchBrief) -> QualityScore:
        """
        Evaluate quality of research brief

        Args:
            brief: ResearchBrief to evaluate

        Returns:
            QualityScore object
        """
        logger.info("Evaluating brief quality")

        # Prepare brief content for evaluation
        brief_text = f"""
EXECUTIVE SUMMARY:
{brief.executive_summary}

TOP INSIGHTS ({len(brief.top_insights)}):
{chr(10).join(f"- {insight}" for insight in brief.top_insights[:5])}

EVIDENCE SOURCES: {len(brief.evidence_table)}
CONTRADICTIONS: {len(brief.contradictions)}
DATA POINTS: {len(brief.data_points)}
GLOSSARY TERMS: {len(brief.glossary)}
"""

        prompt = f"""Evaluate this research brief on three dimensions:

{brief_text}

Rate each dimension 0-100:

1. CLARITY (0-100):
   - Is the writing clear and well-organized?
   - Are concepts explained well?
   - Is the structure logical?

2. CORRECTNESS (0-100):
   - Are claims properly supported?
   - Is evidence credible?
   - Are contradictions acknowledged?

3. COMPLETENESS (0-100):
   - Does it cover the topic thoroughly?
   - Are all promised sections present?
   - Are there significant gaps?

Provide response as JSON:
{{
  "clarity_score": <0-100>,
  "correctness_score": <0-100>,
  "completeness_score": <0-100>,
  "overall_score": <average>,
  "feedback": "<detailed feedback for improvement>",
  "needs_revision": <true/false>
}}
"""

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )

            # Parse quality scores
            score_data = self._parse_quality_response(response.text)

            quality_score = QualityScore(
                clarity_score=score_data["clarity_score"],
                correctness_score=score_data["correctness_score"],
                completeness_score=score_data["completeness_score"],
                overall_score=score_data["overall_score"],
                feedback=score_data["feedback"],
                needs_revision=score_data["needs_revision"]
            )

            logger.info(f"Quality evaluation: {quality_score.overall_score}/100")
            return quality_score

        except Exception as e:
            logger.error(f"Quality evaluation failed: {str(e)}")

            # Fallback: assume decent quality
            return QualityScore(
                clarity_score=75,
                correctness_score=75,
                completeness_score=75,
                overall_score=75,
                feedback="Unable to complete detailed evaluation",
                needs_revision=False
            )

    def _parse_quality_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM response for quality scores

        Args:
            response_text: Raw LLM response

        Returns:
            Dictionary with quality scores
        """
        try:
            # Extract JSON
            if "{" in response_text and "}" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
                data = json.loads(json_str)

                # Validate and clamp scores
                for key in ["clarity_score", "correctness_score", "completeness_score", "overall_score"]:
                    if key in data:
                        data[key] = max(0, min(100, int(data[key])))

                # Calculate overall if not present
                if "overall_score" not in data:
                    data["overall_score"] = int(
                        (data.get("clarity_score", 0) +
                         data.get("correctness_score", 0) +
                         data.get("completeness_score", 0)) / 3
                    )

                # Set needs_revision based on score
                if "needs_revision" not in data:
                    data["needs_revision"] = data["overall_score"] < 90

                return data

        except Exception as e:
            logger.error(f"Quality response parsing failed: {str(e)}")

        # Fallback
        return {
            "clarity_score": 75,
            "correctness_score": 75,
            "completeness_score": 75,
            "overall_score": 75,
            "feedback": "Evaluation incomplete",
            "needs_revision": True
        }

    def improve_brief(self, brief: ResearchBrief, quality_score: QualityScore) -> ResearchBrief:
        """
        Improve research brief based on quality feedback

        Args:
            brief: Current ResearchBrief
            quality_score: Quality evaluation

        Returns:
            Improved ResearchBrief
        """
        logger.info("Improving brief based on feedback")

        # Focus improvement on lowest-scoring dimension
        focus_area = "clarity"
        min_score = quality_score.clarity_score

        if quality_score.correctness_score < min_score:
            focus_area = "correctness"
            min_score = quality_score.correctness_score

        if quality_score.completeness_score < min_score:
            focus_area = "completeness"

        logger.info(f"Focusing improvement on: {focus_area}")

        # Improve executive summary
        if quality_score.clarity_score < 85:
            brief.executive_summary = self._improve_executive_summary(
                brief.executive_summary,
                quality_score.feedback
            )

        # Improve insights if completeness is low
        if quality_score.completeness_score < 85 and len(brief.top_insights) < 10:
            brief.top_insights = self._expand_insights(brief.top_insights, brief.evidence_table)

        # Add more data points if needed
        if quality_score.completeness_score < 85 and len(brief.data_points) < 5:
            # Extract more data points from evidence
            for source in brief.evidence_table[:10]:
                if len(brief.data_points) >= 10:
                    break
                if source.evidence and source.evidence not in brief.data_points:
                    brief.data_points.append(source.evidence[:200])

        logger.info("Brief improvements applied")
        return brief

    def _improve_executive_summary(self, current_summary: str, feedback: str) -> str:
        """
        Improve executive summary based on feedback

        Args:
            current_summary: Current summary text
            feedback: Quality feedback

        Returns:
            Improved summary
        """
        prompt = f"""Improve this executive summary based on the feedback:

CURRENT SUMMARY:
{current_summary}

FEEDBACK:
{feedback}

Rewrite the summary to address the feedback while maintaining accuracy.
Make it clearer, more engaging, and better structured."""

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )

            improved = response.text.strip()
            logger.info("Executive summary improved")
            return improved

        except Exception as e:
            logger.error(f"Summary improvement failed: {str(e)}")
            return current_summary

    def _expand_insights(self, current_insights: list, evidence: list) -> list:
        """
        Expand insights list to reach 10 items

        Args:
            current_insights: Current insights list
            evidence: Evidence table

        Returns:
            Expanded insights list
        """
        if len(current_insights) >= 10:
            return current_insights

        # Add high-quality claims as additional insights
        expanded = current_insights.copy()

        for source in evidence:
            if len(expanded) >= 10:
                break

            if source.reliability_score >= 70 and source.claim not in expanded:
                expanded.append(source.claim)

        return expanded[:10]
