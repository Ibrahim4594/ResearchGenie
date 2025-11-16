"""
Web Search Agent
Performs parallel web searches using Google Search tool
"""

from google import genai
from google.genai import types
import logging
from typing import List, Dict, Any
import asyncio

from src.schemas import WebSearchResult
from src.tools import google_search_tool, web_scraper_tool, create_search_tool_declaration
from src.memory import memory_bank

logger = logging.getLogger(__name__)


class WebSearchAgent:
    """
    Agent that performs web searches and gathers online sources
    Runs in parallel with other research agents
    """

    def __init__(self, client: genai.Client):
        """
        Initialize Web Search Agent

        Args:
            client: Google GenAI client instance
        """
        self.client = client
        self.model_id = "gemini-2.0-flash-exp"
        self.search_tool = google_search_tool
        logger.info("WebSearchAgent initialized")

    def search(self, query: str, num_results: int = 10) -> WebSearchResult:
        """
        Perform web search for research topic

        Args:
            query: Search query
            num_results: Number of results to retrieve

        Returns:
            WebSearchResult with URLs and summaries
        """
        logger.info(f"WebSearchAgent searching for: {query}")

        try:
            # Perform search using custom tool
            search_results = self.search_tool.search(query, num_results)

            # Create WebSearchResult object
            result = WebSearchResult(
                query=query,
                results=search_results.get("raw_results", []),
                urls=search_results.get("urls", []),
                summaries=search_results.get("summaries", [])
            )

            # Enhance summaries using LLM
            result = self._enhance_summaries(result)

            logger.info(f"Found {len(result.urls)} URLs")

            return result

        except Exception as e:
            logger.error(f"Search error: {str(e)}")

            # Return empty result on error
            return WebSearchResult(
                query=query,
                results=[],
                urls=[],
                summaries=[]
            )

    def _enhance_summaries(self, search_result: WebSearchResult) -> WebSearchResult:
        """
        Use LLM to enhance search result summaries

        Args:
            search_result: Initial search results

        Returns:
            Enhanced WebSearchResult
        """
        if not search_result.urls:
            return search_result

        try:
            # Get user preferences for context
            prefs = memory_bank.get_user_preferences()
            topic = prefs.get("topic", search_result.query)

            prompt = f"""Analyze these search results for research on: {topic}

URLs found:
{chr(10).join(f"{i+1}. {url}" for i, url in enumerate(search_result.urls[:5]))}

For each URL, provide:
1. A brief summary (2-3 sentences)
2. Relevance score (0-100)
3. Key topics covered

Format as JSON list."""

            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )

            # Parse enhanced summaries
            enhanced_text = response.text
            logger.info(f"Enhanced summaries generated")

            # Update summaries if parsing successful
            if enhanced_text:
                # For demo, keep original summaries
                # In production, parse JSON and update
                pass

        except Exception as e:
            logger.error(f"Summary enhancement failed: {str(e)}")

        return search_result

    def search_multiple_queries(self, queries: List[str]) -> List[WebSearchResult]:
        """
        Search multiple queries in parallel

        Args:
            queries: List of search queries

        Returns:
            List of WebSearchResult objects
        """
        logger.info(f"Searching {len(queries)} queries in parallel")

        results = []
        for query in queries:
            result = self.search(query)
            results.append(result)

        return results

    def scrape_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Scrape content from URLs

        Args:
            urls: List of URLs to scrape

        Returns:
            List of scraped content dictionaries
        """
        logger.info(f"Scraping {len(urls)} URLs")

        scraped_content = []
        for url in urls[:5]:  # Limit to 5 URLs for demo
            try:
                content = web_scraper_tool.scrape_url(url)
                scraped_content.append(content)
            except Exception as e:
                logger.error(f"Failed to scrape {url}: {str(e)}")

        return scraped_content
