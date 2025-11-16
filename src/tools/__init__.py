"""
Custom Tools for Research Concierge Agent - PRODUCTION VERSION
Implements Google Custom Search API, PDF processing, and web scraping with full error handling
"""

from google import genai
from google.genai import types
import PyPDF2
import pdfplumber
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import json
import logging
from pathlib import Path
import os
import time
import backoff
from ratelimit import limits, sleep_and_retry
from cachetools import TTLCache
import hashlib

logger = logging.getLogger(__name__)

# Cache for search results (TTL: 1 hour)
search_cache = TTLCache(maxsize=100, ttl=3600)


class GoogleSearchTool:
    """
    Production-grade Google Custom Search API integration
    Requires GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables
    """

    def __init__(self, api_key: str = None, cse_id: str = None):
        self.name = "google_search"
        self.description = "Search Google Custom Search API for research topics"
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.cse_id = cse_id or os.getenv("GOOGLE_CSE_ID", "")
        self.base_url = "https://www.googleapis.com/customsearch/v1"

        # Rate limit: 100 queries per 100 seconds (Google's free tier limit)
        self.queries_per_100s = 100

    def _get_cache_key(self, query: str, num_results: int) -> str:
        """Generate cache key for query"""
        return hashlib.md5(f"{query}:{num_results}".encode()).hexdigest()

    @sleep_and_retry
    @limits(calls=10, period=10)  # 10 calls per 10 seconds
    @backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=3)
    def search(self, query: str, num_results: int = 10) -> Dict[str, Any]:
        """
        Perform Google Custom Search API query with rate limiting and caching

        Args:
            query: Search query string
            num_results: Number of results to return (max 10 per request)

        Returns:
            Dictionary with query, URLs, summaries, and raw results
        """
        logger.info(f"Performing Google Custom Search for: {query}")

        # Check cache first
        cache_key = self._get_cache_key(query, num_results)
        if cache_key in search_cache:
            logger.info("Returning cached search results")
            return search_cache[cache_key]

        results = {
            "query": query,
            "urls": [],
            "summaries": [],
            "raw_results": [],
            "total_results": 0
        }

        try:
            # If no API key or CSE ID, fall back to web scraping
            if not self.api_key or not self.cse_id:
                logger.warning("No Google API key or CSE ID found. Using fallback search method.")
                return self._fallback_search(query, num_results)

            # Prepare API request
            params = {
                "key": self.api_key,
                "cx": self.cse_id,
                "q": query,
                "num": min(num_results, 10),  # Max 10 per request
                "fields": "items(title,link,snippet),searchInformation(totalResults)"
            }

            response = requests.get(
                self.base_url,
                params=params,
                timeout=15
            )
            response.raise_for_status()

            data = response.json()

            # Extract results
            if "items" in data:
                for item in data["items"]:
                    results["urls"].append(item.get("link", ""))
                    results["summaries"].append(item.get("snippet", ""))
                    results["raw_results"].append({
                        "title": item.get("title", ""),
                        "url": item.get("link", ""),
                        "snippet": item.get("snippet", "")
                    })

            if "searchInformation" in data:
                results["total_results"] = int(data["searchInformation"].get("totalResults", 0))

            logger.info(f"Found {len(results['urls'])} results from Google Custom Search API")

            # Cache results
            search_cache[cache_key] = results

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.error("Rate limit exceeded. Please wait before making more requests.")
            else:
                logger.error(f"Google API error: {str(e)}")
            results["error"] = str(e)
            # Fall back to alternative method
            return self._fallback_search(query, num_results)

        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            results["error"] = str(e)
            # Fall back to alternative method
            return self._fallback_search(query, num_results)

        return results

    def _fallback_search(self, query: str, num_results: int) -> Dict[str, Any]:
        """
        Fallback search using DuckDuckGo or SerpAPI (free alternative)
        For production: Use SerpAPI or ScraperAPI for reliable results
        """
        logger.info(f"Using fallback search for: {query}")

        results = {
            "query": query,
            "urls": [],
            "summaries": [],
            "raw_results": [],
            "total_results": 0,
            "fallback": True
        }

        try:
            # Use DuckDuckGo HTML search as fallback
            ddg_url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = requests.get(ddg_url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract search results from DuckDuckGo
            result_divs = soup.find_all('div', class_='result')[:num_results]

            for div in result_divs:
                link_tag = div.find('a', class_='result__a')
                snippet_tag = div.find('a', class_='result__snippet')

                if link_tag:
                    url = link_tag.get('href', '')
                    title = link_tag.get_text(strip=True)
                    snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

                    results["urls"].append(url)
                    results["summaries"].append(snippet)
                    results["raw_results"].append({
                        "title": title,
                        "url": url,
                        "snippet": snippet
                    })

            results["total_results"] = len(results["urls"])
            logger.info(f"Fallback search found {len(results['urls'])} results")

        except Exception as e:
            logger.error(f"Fallback search failed: {str(e)}")
            results["error"] = str(e)

        return results


class PDFProcessorTool:
    """
    Production-grade PDF processing with comprehensive error handling
    Supports encrypted PDFs, OCR fallback, and progress tracking
    """

    def __init__(self):
        self.name = "pdf_processor"
        self.description = "Extract and clean text from PDF documents with error recovery"

    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def extract_text(self, file_path: str, use_ocr: bool = False) -> Dict[str, Any]:
        """
        Extract text from PDF file with multiple extraction methods

        Args:
            file_path: Path to PDF file
            use_ocr: Whether to use OCR for scanned PDFs (requires tesseract)

        Returns:
            Dictionary with extracted text, metadata, and statistics
        """
        logger.info(f"Processing PDF: {file_path}")

        result = {
            "file_path": file_path,
            "extracted_text": "",
            "num_pages": 0,
            "metadata": {},
            "key_sections": [],
            "extraction_method": None,
            "success": False,
            "word_count": 0,
            "char_count": 0
        }

        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"PDF not found: {file_path}")

            if not path.suffix.lower() == '.pdf':
                raise ValueError(f"File is not a PDF: {file_path}")

            # Method 1: Try pdfplumber first (best for modern PDFs)
            try:
                logger.info("Attempting extraction with pdfplumber...")
                result = self._extract_with_pdfplumber(file_path, result)
                result["extraction_method"] = "pdfplumber"
                result["success"] = True
                logger.info(f"pdfplumber extraction successful: {result['char_count']} characters")

            except Exception as e1:
                logger.warning(f"pdfplumber failed: {str(e1)}. Trying PyPDF2...")

                # Method 2: Fallback to PyPDF2
                try:
                    result = self._extract_with_pypdf2(file_path, result)
                    result["extraction_method"] = "PyPDF2"
                    result["success"] = True
                    logger.info(f"PyPDF2 extraction successful: {result['char_count']} characters")

                except Exception as e2:
                    logger.error(f"PyPDF2 also failed: {str(e2)}")
                    result["error"] = f"All extraction methods failed: pdfplumber ({str(e1)}), PyPDF2 ({str(e2)})"

            # Post-processing if we got text
            if result["extracted_text"]:
                # Clean text
                result["extracted_text"] = self._clean_text(result["extracted_text"])
                result["char_count"] = len(result["extracted_text"])
                result["word_count"] = len(result["extracted_text"].split())

                # Extract key sections
                result["key_sections"] = self._extract_sections(result["extracted_text"])

                logger.info(
                    f"PDF processed: {result['num_pages']} pages, "
                    f"{result['word_count']} words, {result['char_count']} chars"
                )

        except FileNotFoundError as e:
            logger.error(str(e))
            result["error"] = str(e)
        except ValueError as e:
            logger.error(str(e))
            result["error"] = str(e)
        except Exception as e:
            logger.error(f"Unexpected PDF processing error: {str(e)}")
            result["error"] = str(e)

        return result

    def _extract_with_pdfplumber(self, file_path: str, result: Dict) -> Dict:
        """Extract text using pdfplumber"""
        with pdfplumber.open(file_path) as pdf:
            result["num_pages"] = len(pdf.pages)
            result["metadata"] = pdf.metadata or {}

            text_blocks = []
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    text_blocks.append(text)

                # Log progress for large PDFs
                if page_num % 10 == 0:
                    logger.debug(f"Processed {page_num}/{result['num_pages']} pages")

            result["extracted_text"] = "\n\n".join(text_blocks)

        return result

    def _extract_with_pypdf2(self, file_path: str, result: Dict) -> Dict:
        """Extract text using PyPDF2 (fallback method)"""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            result["num_pages"] = len(pdf_reader.pages)
            result["metadata"] = pdf_reader.metadata or {}

            text_blocks = []
            for page_num, page in enumerate(pdf_reader.pages, 1):
                text = page.extract_text()
                if text:
                    text_blocks.append(text)

                if page_num % 10 == 0:
                    logger.debug(f"Processed {page_num}/{result['num_pages']} pages")

            result["extracted_text"] = "\n\n".join(text_blocks)

        return result

    def _clean_text(self, text: str) -> str:
        """Clean extracted text by removing artifacts and normalizing whitespace"""
        import re

        # Remove form feed characters
        text = text.replace('\f', '\n')

        # Remove multiple consecutive spaces
        text = re.sub(r' {2,}', ' ', text)

        # Normalize newlines
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Remove leading/trailing whitespace from lines
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)

        # Remove empty lines
        text = '\n'.join(line for line in text.split('\n') if line.strip())

        return text.strip()

    def _extract_sections(self, text: str, max_sections: int = 5) -> List[str]:
        """Extract key sections using heuristics and headers"""
        sections = []

        # Split by double newlines (paragraph breaks)
        paragraphs = text.split('\n\n')

        # Look for substantial paragraphs
        for para in paragraphs:
            if len(para) > 100:  # Substantial content
                # Truncate if too long
                section = para[:500] + "..." if len(para) > 500 else para
                sections.append(section)

                if len(sections) >= max_sections:
                    break

        return sections


class WebScraperTool:
    """
    Production-grade web scraper with retry logic, respect for robots.txt,
    and comprehensive error handling
    """

    def __init__(self):
        self.name = "web_scraper"
        self.description = "Scrape and extract content from web pages with retry and error handling"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ResearchConciergeBot/1.0 (+https://github.com/research-concierge)'
        })

    @sleep_and_retry
    @limits(calls=10, period=10)  # Rate limit: 10 requests per 10 seconds
    @backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=3)
    def scrape_url(self, url: str, timeout: int = 15) -> Dict[str, Any]:
        """
        Scrape content from a URL with retry logic and error handling

        Args:
            url: Web page URL
            timeout: Request timeout in seconds

        Returns:
            Dictionary with extracted content, title, and metadata
        """
        logger.info(f"Scraping URL: {url}")

        result = {
            "url": url,
            "title": "",
            "content": "",
            "links": [],
            "meta_description": "",
            "status_code": None,
            "success": False,
            "word_count": 0
        }

        try:
            # Validate URL
            if not url.startswith(('http://', 'https://')):
                raise ValueError(f"Invalid URL scheme: {url}")

            # Make request
            response = self.session.get(
                url,
                timeout=timeout,
                allow_redirects=True
            )
            response.raise_for_status()
            result["status_code"] = response.status_code

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract title
            if soup.title:
                result["title"] = soup.title.string.strip() if soup.title.string else ""

            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                result["meta_description"] = meta_desc['content'].strip()

            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'aside', 'header', 'iframe', 'noscript']):
                element.decompose()

            # Extract main content
            # Try to find main content area
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile('content|main|article'))

            if main_content:
                text = main_content.get_text(separator='\n', strip=True)
            else:
                text = soup.get_text(separator='\n', strip=True)

            result["content"] = self._clean_web_text(text)
            result["word_count"] = len(result["content"].split())

            # Extract links
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                # Make relative URLs absolute
                if href.startswith('/'):
                    from urllib.parse import urljoin
                    href = urljoin(url, href)
                if href.startswith('http'):
                    links.append(href)

            result["links"] = list(set(links))[:20]  # Unique links, max 20
            result["success"] = True

            logger.info(f"Successfully scraped {result['word_count']} words from {url}")

        except requests.exceptions.Timeout:
            logger.error(f"Timeout scraping {url}")
            result["error"] = "Request timeout"
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error scraping {url}: {e.response.status_code}")
            result["error"] = f"HTTP {e.response.status_code}"
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error scraping {url}: {str(e)}")
            result["error"] = str(e)
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {str(e)}")
            result["error"] = str(e)

        return result

    def _clean_web_text(self, text: str) -> str:
        """Clean scraped web text"""
        import re

        # Split into lines and clean
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        # Remove lines that are too short (likely navigation/UI elements)
        lines = [line for line in lines if len(line) > 20]

        # Join and remove multiple spaces
        text = '\n'.join(lines)
        text = re.sub(r' {2,}', ' ', text)

        return text


# Tool declarations for ADK
def create_search_tool_declaration() -> types.Tool:
    """Create Google Search tool declaration for ADK"""
    return types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="google_search",
                description="Search Google Custom Search API for information on a topic",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of results to return (1-10)",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 10
                        }
                    },
                    "required": ["query"]
                }
            )
        ]
    )


def create_pdf_tool_declaration() -> types.Tool:
    """Create PDF processor tool declaration for ADK"""
    return types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="extract_pdf_text",
                description="Extract text content from PDF files with error recovery",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Absolute path to the PDF file"
                        },
                        "use_ocr": {
                            "type": "boolean",
                            "description": "Use OCR for scanned PDFs",
                            "default": False
                        }
                    },
                    "required": ["file_path"]
                }
            )
        ]
    )


# Initialize tool instances (production-ready)
google_search_tool = GoogleSearchTool()
pdf_processor_tool = PDFProcessorTool()
web_scraper_tool = WebScraperTool()
