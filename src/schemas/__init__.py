"""
JSON Schemas for Agent Message Passing
All agents communicate using structured Pydantic models for type safety
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class ResearchScope(str, Enum):
    """Research depth scope"""
    BROAD = "broad"
    DEEP = "deep"
    FOCUSED = "focused"


class WritingStyle(str, Enum):
    """Output writing style"""
    ACADEMIC = "academic"
    CASUAL = "casual"
    TECHNICAL = "technical"
    EXECUTIVE = "executive"


class UserIntent(BaseModel):
    """Schema for User Intent Agent output"""
    topic: str = Field(..., description="Main research topic")
    scope: ResearchScope = Field(..., description="Research depth")
    style: WritingStyle = Field(..., description="Preferred writing style")
    keywords: List[str] = Field(default_factory=list, description="Key search terms")
    constraints: Optional[str] = Field(None, description="Any specific constraints")


class SourceSummary(BaseModel):
    """Schema for individual source summary"""
    claim: str = Field(..., description="Main claim from source")
    evidence: str = Field(..., description="Supporting evidence")
    source_url: str = Field(..., description="URL or file path")
    reliability_score: int = Field(..., ge=0, le=100, description="Reliability 0-100")
    timestamp: Optional[str] = Field(None, description="When sourced")
    source_type: str = Field(default="web", description="Type: web, pdf, document")


class WebSearchResult(BaseModel):
    """Schema for Web Search Agent output"""
    query: str = Field(..., description="Search query used")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Search results")
    urls: List[str] = Field(default_factory=list, description="URLs found")
    summaries: List[str] = Field(default_factory=list, description="Brief summaries")


class DocumentAnalysis(BaseModel):
    """Schema for PDF/Document Agent output"""
    file_path: str = Field(..., description="Path to analyzed file")
    extracted_text: str = Field(..., description="Cleaned extracted text")
    key_sections: List[str] = Field(default_factory=list, description="Important sections")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")


class FactCheckResult(BaseModel):
    """Schema for Fact-Checking Agent output"""
    claim: str = Field(..., description="Claim being checked")
    verdict: str = Field(..., description="True/False/Unverified")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    contradictions: List[str] = Field(default_factory=list, description="Found contradictions")
    supporting_sources: List[str] = Field(default_factory=list, description="Supporting URLs")


class ResearchBrief(BaseModel):
    """Schema for final Synthesis Agent output"""
    executive_summary: str = Field(..., description="Brief overview")
    top_insights: List[str] = Field(..., max_length=10, description="Top 10 insights")
    evidence_table: List[SourceSummary] = Field(default_factory=list, description="All evidence")
    contradictions: List[str] = Field(default_factory=list, description="Contradictory findings")
    data_points: List[str] = Field(default_factory=list, description="Important data")
    glossary: Dict[str, str] = Field(default_factory=dict, description="Key terms")
    suggested_reading: List[str] = Field(default_factory=list, description="Further reading")
    next_questions: List[str] = Field(default_factory=list, description="Follow-up questions")


class QualityScore(BaseModel):
    """Schema for Quality Loop Agent evaluation"""
    clarity_score: int = Field(..., ge=0, le=100, description="Clarity score")
    correctness_score: int = Field(..., ge=0, le=100, description="Correctness score")
    completeness_score: int = Field(..., ge=0, le=100, description="Completeness score")
    overall_score: int = Field(..., ge=0, le=100, description="Overall quality score")
    feedback: str = Field(..., description="Detailed feedback for improvement")
    needs_revision: bool = Field(..., description="Whether revision is needed")
