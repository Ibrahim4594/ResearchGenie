"""
Synthesis Agent
Aggregates all sources and produces final Research Brief
"""

from google import genai
from google.genai import types
import logging
from typing import List, Dict, Any
import json

from src.schemas import SourceSummary, FactCheckResult, ResearchBrief
from src.memory import memory_bank

logger = logging.getLogger(__name__)


class SynthesisAgent:
    """
    Agent that synthesizes all research into comprehensive brief
    Creates executive summary, insights, evidence table, etc.
    """

    def __init__(self, client: genai.Client):
        """
        Initialize Synthesis Agent

        Args:
            client: Google GenAI client instance
        """
        self.client = client
        self.model_id = "gemini-2.0-flash-exp"
        logger.info("SynthesisAgent initialized")

    def synthesize(
        self,
        sources: List[SourceSummary],
        fact_checks: List[FactCheckResult],
        contradictions: List[str]
    ) -> ResearchBrief:
        """
        Synthesize all research into final brief

        Args:
            sources: List of all source summaries
            fact_checks: List of fact check results
            contradictions: List of contradictions found

        Returns:
            ResearchBrief object
        """
        logger.info(f"Synthesizing research from {len(sources)} sources")

        # Get user preferences for style
        prefs = memory_bank.get_user_preferences()
        topic = prefs.get("topic", "the research topic")
        style = prefs.get("style", "casual")

        try:
            # Generate executive summary
            exec_summary = self._generate_executive_summary(sources, topic, style)

            # Generate top insights
            top_insights = self._generate_insights(sources, fact_checks)

            # Extract important data points
            data_points = self._extract_data_points(sources)

            # Build glossary
            glossary = self._build_glossary(sources)

            # Generate suggested reading
            suggested_reading = self._generate_suggested_reading(sources)

            # Generate next questions
            next_questions = self._generate_next_questions(topic, sources)

            # Create ResearchBrief
            brief = ResearchBrief(
                executive_summary=exec_summary,
                top_insights=top_insights[:10],  # Limit to 10
                evidence_table=sources,
                contradictions=contradictions,
                data_points=data_points,
                glossary=glossary,
                suggested_reading=suggested_reading,
                next_questions=next_questions
            )

            logger.info("Research brief synthesized successfully")
            return brief

        except Exception as e:
            logger.error(f"Synthesis failed: {str(e)}")

            # Return minimal brief on error
            return ResearchBrief(
                executive_summary=f"Research on {topic} - synthesis incomplete",
                top_insights=["Unable to generate insights"],
                evidence_table=sources,
                contradictions=contradictions,
                data_points=[],
                glossary={},
                suggested_reading=[],
                next_questions=[]
            )

    def _generate_executive_summary(
        self,
        sources: List[SourceSummary],
        topic: str,
        style: str
    ) -> str:
        """
        Generate executive summary using LLM

        Args:
            sources: Source summaries
            topic: Research topic
            style: Writing style

        Returns:
            Executive summary text
        """
        # Prepare context from sources
        context = "\n".join([
            f"- {s.claim} (reliability: {s.reliability_score}%)"
            for s in sources[:10]
        ])

        prompt = f"""Write an executive summary for research on: {topic}

Based on these key findings:
{context}

Style: {style}

Write a comprehensive yet concise executive summary (3-5 paragraphs) that:
1. States the main topic and scope
2. Highlights key findings
3. Notes important trends or patterns
4. Mentions any limitations or contradictions

Keep it clear and {style}."""

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )

            summary = response.text.strip()
            logger.info("Executive summary generated")
            return summary

        except Exception as e:
            logger.error(f"Executive summary generation failed: {str(e)}")
            return f"Research on {topic} compiled from {len(sources)} sources."

    def _generate_insights(
        self,
        sources: List[SourceSummary],
        fact_checks: List[FactCheckResult]
    ) -> List[str]:
        """
        Generate top insights from research

        Args:
            sources: Source summaries
            fact_checks: Fact check results

        Returns:
            List of insight strings
        """
        # Use high-reliability sources
        high_quality = [s for s in sources if s.reliability_score >= 70]

        context = "\n".join([
            s.claim for s in high_quality[:15]
        ])

        prompt = f"""Based on this research, extract the top 10 key insights:

{context}

Format as a numbered list. Each insight should be:
- Specific and actionable
- Supported by the evidence
- Clear and concise (1-2 sentences)
"""

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )

            # Parse numbered list
            insights = []
            for line in response.text.split('\n'):
                line = line.strip()
                # Remove numbering
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
                    # Strip numbering
                    clean_line = line.lstrip('0123456789.-*) ').strip()
                    if clean_line:
                        insights.append(clean_line)

            logger.info(f"Generated {len(insights)} insights")
            return insights[:10]

        except Exception as e:
            logger.error(f"Insight generation failed: {str(e)}")

            # Fallback: use top claims
            return [s.claim for s in sources[:10]]

    def _extract_data_points(self, sources: List[SourceSummary]) -> List[str]:
        """
        Extract important data points from sources

        Args:
            sources: Source summaries

        Returns:
            List of data point strings
        """
        data_points = []

        # Look for numbers, percentages, dates in evidence
        import re

        for source in sources:
            text = f"{source.claim} {source.evidence}"

            # Find patterns like: "42%", "$1.5M", "2024", "1,000 users"
            patterns = [
                r'\d+%',  # Percentages
                r'\$[\d,]+\.?\d*[KMB]?',  # Money
                r'\d{4}(?:\s*-\s*\d{4})?',  # Years
                r'\d+(?:,\d{3})*(?:\.\d+)?',  # Numbers
            ]

            for pattern in patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    # Get context around the number
                    idx = text.find(match)
                    context_start = max(0, idx - 50)
                    context_end = min(len(text), idx + len(match) + 50)
                    context = text[context_start:context_end].strip()

                    data_points.append(context)

                    if len(data_points) >= 10:
                        break

            if len(data_points) >= 10:
                break

        logger.info(f"Extracted {len(data_points)} data points")
        return data_points[:10]

    def _build_glossary(self, sources: List[SourceSummary]) -> Dict[str, str]:
        """
        Build glossary of key terms

        Args:
            sources: Source summaries

        Returns:
            Dictionary mapping terms to definitions
        """
        # Combine all text
        all_text = " ".join([f"{s.claim} {s.evidence}" for s in sources[:20]])

        prompt = f"""From this research text, identify 5-8 key technical terms or jargon and provide clear definitions.

Text:
{all_text[:2000]}

Format as JSON object with term: definition pairs."""

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )

            # Parse JSON
            if "{" in response.text and "}" in response.text:
                start = response.text.find("{")
                end = response.text.rfind("}") + 1
                json_str = response.text[start:end]
                glossary = json.loads(json_str)

                logger.info(f"Built glossary with {len(glossary)} terms")
                return glossary

        except Exception as e:
            logger.error(f"Glossary building failed: {str(e)}")

        return {}

    def _generate_suggested_reading(self, sources: List[SourceSummary]) -> List[str]:
        """
        Generate suggested reading list from sources

        Args:
            sources: Source summaries

        Returns:
            List of URLs/references
        """
        # Sort by reliability
        sorted_sources = sorted(sources, key=lambda s: s.reliability_score, reverse=True)

        # Take top 5-10 sources
        suggested = []
        for source in sorted_sources[:10]:
            if source.source_type == "web":
                suggested.append(f"{source.claim[:100]} - {source.source_url}")
            else:
                suggested.append(f"{source.claim[:100]} - {source.source_url}")

        logger.info(f"Generated {len(suggested)} reading suggestions")
        return suggested

    def _generate_next_questions(self, topic: str, sources: List[SourceSummary]) -> List[str]:
        """
        Generate follow-up research questions

        Args:
            topic: Research topic
            sources: Source summaries

        Returns:
            List of question strings
        """
        context = "\n".join([s.claim for s in sources[:10]])

        prompt = f"""Based on this research on {topic}, generate 5-7 important follow-up questions that would deepen understanding or address gaps.

Current findings:
{context}

Format as a numbered list of questions."""

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )

            # Parse questions
            questions = []
            for line in response.text.split('\n'):
                line = line.strip()
                if line and '?' in line:
                    clean_line = line.lstrip('0123456789.-*) ').strip()
                    if clean_line:
                        questions.append(clean_line)

            logger.info(f"Generated {len(questions)} follow-up questions")
            return questions[:7]

        except Exception as e:
            logger.error(f"Question generation failed: {str(e)}")
            return [f"What are the latest developments in {topic}?"]
