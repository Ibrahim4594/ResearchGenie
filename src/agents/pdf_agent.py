"""
PDF/Document Agent
Extracts and processes PDF and text documents
Supports pause/resume for long-running operations
"""

from google import genai
from google.genai import types
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.schemas import DocumentAnalysis
from src.tools import pdf_processor_tool
from src.memory import session_manager

logger = logging.getLogger(__name__)


class PDFDocumentAgent:
    """
    Agent for processing PDF and document files
    Uses code execution tool and supports long-running operations
    """

    def __init__(self, client: genai.Client):
        """
        Initialize PDF Document Agent

        Args:
            client: Google GenAI client instance
        """
        self.client = client
        self.model_id = "gemini-2.0-flash-exp"
        self.pdf_tool = pdf_processor_tool
        logger.info("PDFDocumentAgent initialized")

    def process_document(self, file_path: str, session_id: Optional[str] = None) -> DocumentAnalysis:
        """
        Process a PDF or text document

        Args:
            file_path: Path to document file
            session_id: Optional session ID for pause/resume

        Returns:
            DocumentAnalysis object with extracted content
        """
        logger.info(f"Processing document: {file_path}")

        # Create or resume session for long-running ops
        if session_id:
            session = session_manager.get_session(session_id)
            if session and session.get("status") == "paused":
                logger.info(f"Resuming session: {session_id}")
                session_manager.resume_session(session_id)
        else:
            session_id = f"pdf_{Path(file_path).stem}"
            session_manager.create_session(session_id, {"file_path": file_path})

        try:
            # Check file type
            file_ext = Path(file_path).suffix.lower()

            if file_ext == '.pdf':
                result = self._process_pdf(file_path, session_id)
            elif file_ext in ['.txt', '.md']:
                result = self._process_text_file(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")

            # Save session state
            session_manager.save_session_state(session_id, {
                "file_path": file_path,
                "completed": True,
                "num_chars": len(result.extracted_text)
            })

            logger.info(f"Document processed: {len(result.extracted_text)} characters extracted")

            return result

        except Exception as e:
            logger.error(f"Document processing error: {str(e)}")

            # Pause session on error for retry
            session_manager.pause_session(session_id)

            # Return minimal result
            return DocumentAnalysis(
                file_path=file_path,
                extracted_text="",
                key_sections=[],
                metadata={"error": str(e)}
            )

    def _process_pdf(self, file_path: str, session_id: str) -> DocumentAnalysis:
        """
        Process PDF file using custom tool

        Args:
            file_path: Path to PDF
            session_id: Session ID for tracking

        Returns:
            DocumentAnalysis object
        """
        # Use PDF processor tool
        pdf_data = self.pdf_tool.extract_text(file_path)

        # Create analysis object
        analysis = DocumentAnalysis(
            file_path=file_path,
            extracted_text=pdf_data.get("extracted_text", ""),
            key_sections=pdf_data.get("key_sections", []),
            metadata={
                "num_pages": pdf_data.get("num_pages", 0),
                "source_metadata": pdf_data.get("metadata", {}),
                "session_id": session_id
            }
        )

        # Enhance with LLM analysis
        analysis = self._enhance_with_llm(analysis)

        return analysis

    def _process_text_file(self, file_path: str) -> DocumentAnalysis:
        """
        Process plain text file

        Args:
            file_path: Path to text file

        Returns:
            DocumentAnalysis object
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            # Split into sections (by double newlines)
            sections = [s.strip() for s in text.split('\n\n') if s.strip()]
            key_sections = sections[:5]  # First 5 sections

            analysis = DocumentAnalysis(
                file_path=file_path,
                extracted_text=text,
                key_sections=key_sections,
                metadata={"file_type": "text"}
            )

            return analysis

        except Exception as e:
            logger.error(f"Text file processing error: {str(e)}")
            return DocumentAnalysis(
                file_path=file_path,
                extracted_text="",
                key_sections=[],
                metadata={"error": str(e)}
            )

    def _enhance_with_llm(self, analysis: DocumentAnalysis) -> DocumentAnalysis:
        """
        Use LLM to enhance document analysis

        Args:
            analysis: Initial analysis

        Returns:
            Enhanced DocumentAnalysis
        """
        if not analysis.extracted_text:
            return analysis

        try:
            # Truncate text for LLM (use first 5000 chars)
            text_sample = analysis.extracted_text[:5000]

            prompt = f"""Analyze this document excerpt and provide:
1. Main topics (list)
2. Key findings (list)
3. Document type (research paper, report, article, etc.)

Document excerpt:
{text_sample}

Provide analysis as JSON."""

            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )

            # Add LLM analysis to metadata
            analysis.metadata["llm_analysis"] = response.text
            logger.info("Document enhanced with LLM analysis")

        except Exception as e:
            logger.error(f"LLM enhancement failed: {str(e)}")

        return analysis

    def process_multiple_documents(self, file_paths: List[str]) -> List[DocumentAnalysis]:
        """
        Process multiple documents

        Args:
            file_paths: List of file paths

        Returns:
            List of DocumentAnalysis objects
        """
        logger.info(f"Processing {len(file_paths)} documents")

        results = []
        for file_path in file_paths:
            analysis = self.process_document(file_path)
            results.append(analysis)

        return results
