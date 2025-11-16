"""
User Intent Agent
Extracts research topic, scope, style from user input and stores in MemoryBank
"""

from google import genai
from google.genai import types
import logging
from typing import Dict, Any
import json

from src.schemas import UserIntent, ResearchScope, WritingStyle
from src.memory import memory_bank

logger = logging.getLogger(__name__)


class UserIntentAgent:
    """
    Agent that analyzes user input to extract research intent
    Uses ADK Agent framework with structured output
    """

    def __init__(self, client: genai.Client):
        """
        Initialize User Intent Agent

        Args:
            client: Google GenAI client instance
        """
        self.client = client
        self.model_id = "gemini-2.0-flash-exp"
        logger.info("UserIntentAgent initialized")

    def analyze_intent(self, user_query: str) -> UserIntent:
        """
        Analyze user query to extract research intent

        Args:
            user_query: User's research request

        Returns:
            UserIntent object with extracted information
        """
        logger.info(f"Analyzing user intent for query: {user_query[:100]}...")

        # Create a prompt for intent extraction
        system_prompt = """You are an expert research assistant that analyzes user queries.

Extract the following from the user's research request:
1. Main topic/subject
2. Research scope (broad, deep, or focused)
3. Writing style preference (academic, casual, technical, or executive)
4. Key search keywords
5. Any specific constraints or requirements

Return your analysis in JSON format with keys: topic, scope, style, keywords, constraints.

Examples:
- "I need a deep dive into quantum computing" → scope: deep, style: technical
- "Quick overview of climate change" → scope: broad, style: casual
- "Comprehensive analysis of market trends for executives" → scope: deep, style: executive
"""

        try:
            # Use ADK's generate_content with structured prompting
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=f"{system_prompt}\n\nUser query: {user_query}\n\nProvide JSON analysis:"
            )

            # Parse response
            result_text = response.text

            # Extract JSON from response
            intent_data = self._parse_intent_response(result_text, user_query)

            # Create UserIntent object
            user_intent = UserIntent(
                topic=intent_data.get("topic", user_query),
                scope=ResearchScope(intent_data.get("scope", "broad")),
                style=WritingStyle(intent_data.get("style", "casual")),
                keywords=intent_data.get("keywords", []),
                constraints=intent_data.get("constraints")
            )

            # Store in MemoryBank
            memory_bank.store_user_preferences({
                "topic": user_intent.topic,
                "scope": user_intent.scope.value,
                "style": user_intent.style.value,
                "keywords": user_intent.keywords,
                "constraints": user_intent.constraints
            })

            logger.info(f"Intent extracted - Topic: {user_intent.topic}, Scope: {user_intent.scope}")

            return user_intent

        except Exception as e:
            logger.error(f"Error analyzing intent: {str(e)}")

            # Fallback: create basic intent from query
            fallback_intent = UserIntent(
                topic=user_query,
                scope=ResearchScope.BROAD,
                style=WritingStyle.CASUAL,
                keywords=user_query.split()[:5],
                constraints=None
            )

            memory_bank.store_user_preferences({
                "topic": fallback_intent.topic,
                "scope": fallback_intent.scope.value,
                "style": fallback_intent.style.value,
                "keywords": fallback_intent.keywords
            })

            return fallback_intent

    def _parse_intent_response(self, response_text: str, user_query: str) -> Dict[str, Any]:
        """
        Parse LLM response to extract intent data

        Args:
            response_text: Raw response from model
            user_query: Original user query

        Returns:
            Dictionary with intent fields
        """
        try:
            # Try to extract JSON
            if "{" in response_text and "}" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
                intent_data = json.loads(json_str)
                return intent_data
        except:
            pass

        # Fallback parsing
        intent_data = {
            "topic": user_query,
            "scope": "broad",
            "style": "casual",
            "keywords": user_query.split()[:5],
            "constraints": None
        }

        # Simple keyword detection for scope
        if any(word in user_query.lower() for word in ["deep", "comprehensive", "detailed", "thorough"]):
            intent_data["scope"] = "deep"
        elif any(word in user_query.lower() for word in ["quick", "brief", "overview", "summary"]):
            intent_data["scope"] = "broad"

        # Simple detection for style
        if any(word in user_query.lower() for word in ["academic", "research", "scientific"]):
            intent_data["style"] = "academic"
        elif any(word in user_query.lower() for word in ["technical", "engineering"]):
            intent_data["style"] = "technical"
        elif any(word in user_query.lower() for word in ["executive", "business", "management"]):
            intent_data["style"] = "executive"

        return intent_data

    def get_stored_preferences(self) -> Dict[str, Any]:
        """
        Retrieve stored user preferences from MemoryBank

        Returns:
            Dictionary with user preferences
        """
        return memory_bank.get_user_preferences()
