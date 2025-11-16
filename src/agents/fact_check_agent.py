"""
Fact-Checking Agent
Verifies claims and identifies contradictions across sources
"""

from google import genai
from google.genai import types
import logging
from typing import List, Dict, Any
import json

from src.schemas import SourceSummary, FactCheckResult
from src.memory import memory_bank

logger = logging.getLogger(__name__)


class FactCheckAgent:
    """
    Agent that fact-checks claims and identifies contradictions
    Cross-references multiple sources
    """

    def __init__(self, client: genai.Client):
        """
        Initialize Fact-Check Agent

        Args:
            client: Google GenAI client instance
        """
        self.client = client
        self.model_id = "gemini-2.0-flash-exp"
        logger.info("FactCheckAgent initialized")

    def check_claim(self, claim: str, sources: List[SourceSummary]) -> FactCheckResult:
        """
        Fact-check a single claim against sources

        Args:
            claim: Claim to verify
            sources: List of source summaries to check against

        Returns:
            FactCheckResult object
        """
        logger.info(f"Fact-checking claim: {claim[:100]}...")

        try:
            # Gather evidence from sources
            evidence_list = []
            for source in sources:
                if claim.lower() in source.claim.lower() or claim.lower() in source.evidence.lower():
                    evidence_list.append({
                        "claim": source.claim,
                        "evidence": source.evidence,
                        "url": source.source_url,
                        "reliability": source.reliability_score
                    })

            # Use LLM to analyze claim
            result = self._analyze_claim_with_llm(claim, evidence_list)

            # Store in memory bank
            memory_bank.add_fact_check(result.dict())

            return result

        except Exception as e:
            logger.error(f"Fact check failed: {str(e)}")

            return FactCheckResult(
                claim=claim,
                verdict="Unverified",
                confidence=0.0,
                contradictions=[],
                supporting_sources=[]
            )

    def _analyze_claim_with_llm(self, claim: str, evidence_list: List[Dict[str, Any]]) -> FactCheckResult:
        """
        Use LLM to analyze claim against evidence

        Args:
            claim: Claim to check
            evidence_list: List of evidence dictionaries

        Returns:
            FactCheckResult
        """
        # Prepare evidence context
        evidence_context = "\n".join([
            f"- {ev['claim']} (reliability: {ev['reliability']}%)"
            for ev in evidence_list[:5]
        ])

        prompt = f"""Fact-check this claim using the provided evidence:

CLAIM: {claim}

EVIDENCE:
{evidence_context if evidence_context else "No direct evidence found"}

Analyze and provide:
1. Verdict: "True", "False", or "Unverified"
2. Confidence: 0.0 to 1.0
3. Contradictions: List any contradictory information
4. Supporting sources: List evidence that supports the claim

Provide response as JSON with keys: verdict, confidence, contradictions (list), supporting_info"""

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )

            # Parse response
            result_data = self._parse_fact_check_response(response.text)

            fact_check_result = FactCheckResult(
                claim=claim,
                verdict=result_data.get("verdict", "Unverified"),
                confidence=float(result_data.get("confidence", 0.5)),
                contradictions=result_data.get("contradictions", []),
                supporting_sources=[ev["url"] for ev in evidence_list if ev.get("url")]
            )

            return fact_check_result

        except Exception as e:
            logger.error(f"LLM fact check failed: {str(e)}")

            return FactCheckResult(
                claim=claim,
                verdict="Unverified",
                confidence=0.0,
                contradictions=[],
                supporting_sources=[]
            )

    def _parse_fact_check_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM response for fact check data

        Args:
            response_text: Raw LLM response

        Returns:
            Dictionary with verdict, confidence, contradictions
        """
        try:
            # Try JSON extraction
            if "{" in response_text and "}" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
                data = json.loads(json_str)

                # Ensure confidence is float 0-1
                if "confidence" in data:
                    conf = float(data["confidence"])
                    data["confidence"] = max(0.0, min(1.0, conf))

                return data

        except Exception as e:
            logger.error(f"Fact check parsing failed: {str(e)}")

        # Fallback
        return {
            "verdict": "Unverified",
            "confidence": 0.5,
            "contradictions": [],
            "supporting_info": ""
        }

    def check_all_claims(self, sources: List[SourceSummary]) -> List[FactCheckResult]:
        """
        Fact-check all claims from sources

        Args:
            sources: List of SourceSummary objects

        Returns:
            List of FactCheckResult objects
        """
        logger.info(f"Fact-checking {len(sources)} sources")

        results = []

        # Extract unique claims
        claims_set = set()
        for source in sources:
            if source.claim and len(source.claim) > 20:
                claims_set.add(source.claim)

        # Check each unique claim
        for claim in list(claims_set)[:10]:  # Limit to 10 for demo
            result = self.check_claim(claim, sources)
            results.append(result)

        logger.info(f"Completed {len(results)} fact checks")
        return results

    def find_contradictions(self, sources: List[SourceSummary]) -> List[str]:
        """
        Find contradictions across sources

        Args:
            sources: List of SourceSummary objects

        Returns:
            List of contradiction descriptions
        """
        logger.info("Searching for contradictions")

        contradictions = []

        # Group sources by topic similarity
        # For demo, use simple keyword matching
        topics = {}
        for source in sources:
            # Extract first few words as topic
            words = source.claim.split()[:3]
            topic_key = " ".join(words).lower()

            if topic_key not in topics:
                topics[topic_key] = []
            topics[topic_key].append(source)

        # Check for contradictions within topics
        for topic, topic_sources in topics.items():
            if len(topic_sources) > 1:
                # Use LLM to detect contradictions
                contradiction = self._detect_contradiction(topic_sources)
                if contradiction:
                    contradictions.append(contradiction)

        logger.info(f"Found {len(contradictions)} contradictions")
        return contradictions

    def _detect_contradiction(self, sources: List[SourceSummary]) -> str:
        """
        Detect contradictions in a group of related sources

        Args:
            sources: List of related SourceSummary objects

        Returns:
            Contradiction description or empty string
        """
        if len(sources) < 2:
            return ""

        try:
            claims_text = "\n".join([
                f"{i+1}. {s.claim} (reliability: {s.reliability_score}%)"
                for i, s in enumerate(sources[:5])
            ])

            prompt = f"""Analyze these related claims for contradictions:

{claims_text}

If you find contradictions, describe them clearly.
If no contradictions, respond with "No contradictions found."
"""

            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )

            result = response.text.strip()

            if "no contradictions" in result.lower():
                return ""

            return result[:500]  # Limit length

        except Exception as e:
            logger.error(f"Contradiction detection failed: {str(e)}")
            return ""
