"""Pydantic schemas for enforced JSON structured outputs."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SourceCitation(BaseModel):
    """Citation reference from RAG retrieval."""
    document_id: str = Field(description="Identifier or title of the source document")
    content_snippet: str = Field(description="Relevant text excerpt from source document")
    score: Optional[float] = Field(default=None, description="Similarity score of the retrieved chunk")


class ToolExecutionRecord(BaseModel):
    """Record of a tool call executed during generation."""
    tool_name: str = Field(description="Name of the tool executed")
    arguments: Dict[str, Any] = Field(description="Arguments supplied to the tool")
    result: Any = Field(description="Output returned by the tool")


class AssistantResponse(BaseModel):
    """Standardized structured output format for the AI Assistant."""
    answer: str = Field(description="Main textual response provided by the assistant")
    citations: List[SourceCitation] = Field(default_factory=list, description="List of source citations used")
    tools_used: List[ToolExecutionRecord] = Field(default_factory=list, description="List of tool calls executed")
    confidence_score: Optional[float] = Field(default=1.0, ge=0.0, le=1.0, description="Confidence estimate of the response")
    provider_used: Optional[str] = Field(default=None, description="The LLM provider that generated the response")
    cached: bool = Field(default=False, description="Whether the response was retrieved from cache")
    latency_ms: Optional[float] = Field(default=None, description="Total generation time in milliseconds")


class ExtractionResult(BaseModel):
    """General structured data extraction schema."""
    summary: str = Field(description="Brief summary of the input text")
    key_points: List[str] = Field(description="Extracted key bullet points")
    entities: List[Dict[str, str]] = Field(default_factory=list, description="Named entities and categories")
    sentiment: Optional[str] = Field(default="neutral", description="Detected sentiment: positive, negative, neutral")
