"""
Source Summarizer Agent
Converts raw sources into structured summaries with reliability scores
"""

from google import genai
from google.genai import types
import logging
from typing import List, Dict, Any
import json
from datetime import datetime

from src.schemas import SourceSummary, WebSearchResult, DocumentAnalysis
from src.memory import memory_bank

logger = logging.getLogger(__name__)


class SourceSummarizerAgent:
    """
    Agent that summarizes sources into structured format
    Extracts claims, evidence, and assigns reliability scores
    """

    def __init__(self, client: genai.Client):
        """
        Initialize Source Summarizer Agent

        Args:
            client: Google GenAI client instance
        """
        self.client = client
        self.model_id = "gemini-2.0-flash-exp"
        logger.info("SourceSummarizerAgent initialized")

    def summarize_web_results(self, search_results: WebSearchResult) -> List[SourceSummary]:
        """
        Summarize web search results

        Args:
            search_results: WebSearchResult object

        Returns:
            List of SourceSummary objects
        """
        logger.info(f"Summarizing {len(search_results.urls)} web sources")

        summaries = []

        for i, url in enumerate(search_results.urls):
            try:
                summary_text = search_results.summaries[i] if i < len(search_results.summaries) else ""

                # Use LLM to create structured summary
                source_summary = self._create_source_summary(
                    content=summary_text,
                    source_url=url,
                    source_type="web"
                )

                summaries.append(source_summary)

                # Store in memory bank
                memory_bank.add_source(source_summary.dict())

            except Exception as e:
                logger.error(f"Failed to summarize {url}: {str(e)}")

        logger.info(f"Created {len(summaries)} source summaries")
        return summaries

    def summarize_document(self, doc_analysis: DocumentAnalysis) -> List[SourceSummary]:
        """
        Summarize document analysis into source summaries

        Args:
            doc_analysis: DocumentAnalysis object

        Returns:
            List of SourceSummary objects (one per key section)
        """
        logger.info(f"Summarizing document: {doc_analysis.file_path}")

        summaries = []

        # Summarize key sections
        for section in doc_analysis.key_sections[:5]:
            try:
                source_summary = self._create_source_summary(
                    content=section,
                    source_url=doc_analysis.file_path,
                    source_type="document"
                )

                summaries.append(source_summary)
                memory_bank.add_source(source_summary.dict())

            except Exception as e:
                logger.error(f"Failed to summarize section: {str(e)}")

        # Also create overall document summary
        if doc_analysis.extracted_text:
            try:
                overall_summary = self._create_source_summary(
                    content=doc_analysis.extracted_text[:2000],  # First 2000 chars
                    source_url=doc_analysis.file_path,
                    source_type="document"
                )
                summaries.append(overall_summary)
                memory_bank.add_source(overall_summary.dict())

            except Exception as e:
                logger.error(f"Failed to create overall summary: {str(e)}")

        logger.info(f"Created {len(summaries)} document summaries")
        return summaries

    def _create_source_summary(
        self,
        content: str,
        source_url: str,
        source_type: str
    ) -> SourceSummary:
        """
        Create structured SourceSummary using LLM

        Args:
            content: Source content text
            source_url: URL or file path
            source_type: Type of source (web, document, etc.)

        Returns:
            SourceSummary object
        """
        try:
            prompt = f"""Analyze this source and extract:
1. Main claim or finding
2. Supporting evidence
3. Reliability score (0-100) based on:
   - Clarity of evidence
   - Specificity of claims
   - Presence of data/citations

Source content:
{content[:1500]}

Provide response as JSON with keys: claim, evidence, reliability_score"""

            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )

            # Parse response
            summary_data = self._parse_summary_response(response.text)

            source_summary = SourceSummary(
                claim=summary_data.get("claim", content[:200]),
                evidence=summary_data.get("evidence", content[:300]),
                source_url=source_url,
                reliability_score=summary_data.get("reliability_score", 50),
                timestamp=datetime.now().isoformat(),
                source_type=source_type
            )

            return source_summary

        except Exception as e:
            logger.error(f"Summary creation failed: {str(e)}")

            # Fallback: create basic summary
            return SourceSummary(
                claim=content[:200] if content else "No content available",
                evidence=content[:300] if content else "",
                source_url=source_url,
                reliability_score=50,
                timestamp=datetime.now().isoformat(),
                source_type=source_type
            )

    def _parse_summary_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM response to extract summary data

        Args:
            response_text: Raw LLM response

        Returns:
            Dictionary with claim, evidence, reliability_score
        """
        try:
            # Try to extract JSON
            if "{" in response_text and "}" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
                data = json.loads(json_str)

                # Ensure reliability_score is int 0-100
                if "reliability_score" in data:
                    score = int(data["reliability_score"])
                    data["reliability_score"] = max(0, min(100, score))

                return data

        except Exception as e:
            logger.error(f"JSON parsing failed: {str(e)}")

        # Fallback parsing
        return {
            "claim": "Unable to extract claim",
            "evidence": "Unable to extract evidence",
            "reliability_score": 50
        }

    def summarize_all_sources(
        self,
        web_results: List[WebSearchResult],
        doc_analyses: List[DocumentAnalysis]
    ) -> List[SourceSummary]:
        """
        Summarize all sources (web + documents)

        Args:
            web_results: List of WebSearchResult objects
            doc_analyses: List of DocumentAnalysis objects

        Returns:
            Combined list of all SourceSummary objects
        """
        logger.info("Summarizing all sources")

        all_summaries = []

        # Summarize web results
        for web_result in web_results:
            summaries = self.summarize_web_results(web_result)
            all_summaries.extend(summaries)

        # Summarize documents
        for doc_analysis in doc_analyses:
            summaries = self.summarize_document(doc_analysis)
            all_summaries.extend(summaries)

        logger.info(f"Total summaries created: {len(all_summaries)}")
        return all_summaries
