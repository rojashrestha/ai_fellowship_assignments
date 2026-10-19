"""
Core data models and schema definitions for the Trustworthy AI Guardrail System.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ActionTaken(str, Enum):
    ALLOW = "ALLOW"
    REDACT = "REDACT"
    BLOCK = "BLOCK"
    REGENERATE = "REGENERATE"
    SAFE_FALLBACK = "SAFE_FALLBACK"


class GuardrailStatus(str, Enum):
    PASSED = "PASSED"
    FLAGGED = "FLAGGED"
    BLOCKED = "BLOCKED"
    REDACTED = "REDACTED"
    FALLBACK = "FALLBACK"


@dataclass
class GuardrailResult:
    guardrail_name: str
    passed: bool
    action: ActionTaken
    details: Dict[str, Any] = field(default_factory=dict)
    sanitized_text: Optional[str] = None
    risk_score: float = 0.0
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "guardrail_name": self.guardrail_name,
            "passed": self.passed,
            "action": self.action.value,
            "risk_score": round(self.risk_score, 3),
            "message": self.message,
            "details": self.details,
            "sanitized_text": self.sanitized_text,
        }


@dataclass
class InputGuardrailReport:
    passed: bool
    sanitized_input: str
    results: List[GuardrailResult] = field(default_factory=list)
    blocked_reason: Optional[str] = None
    primary_action: ActionTaken = ActionTaken.ALLOW

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "primary_action": self.primary_action.value,
            "blocked_reason": self.blocked_reason,
            "sanitized_input": self.sanitized_input,
            "checks": [r.to_dict() for r in self.results],
        }


@dataclass
class StructuredAIResponse:
    """Standardized response schema expected from AI model."""
    status: str
    answer: str
    confidence_score: float
    citations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "answer": self.answer,
            "confidence_score": self.confidence_score,
            "citations": self.citations,
            "metadata": self.metadata,
        }


@dataclass
class OutputGuardrailReport:
    passed: bool
    final_response: Optional[Dict[str, Any]] = None
    results: List[GuardrailResult] = field(default_factory=list)
    action_taken: ActionTaken = ActionTaken.ALLOW
    fallback_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "action_taken": self.action_taken.value,
            "fallback_reason": self.fallback_reason,
            "final_response": self.final_response,
            "checks": [r.to_dict() for r in self.results],
        }


@dataclass
class PipelineResult:
    query: str
    sanitized_query: str
    reference_context: Optional[str]
    input_report: InputGuardrailReport
    raw_ai_response: Optional[Any]
    output_report: Optional[OutputGuardrailReport]
    final_output: Dict[str, Any]
    success: bool
    latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "sanitized_query": self.sanitized_query,
            "success": self.success,
            "latency_ms": round(self.latency_ms, 2),
            "input_report": self.input_report.to_dict(),
            "raw_ai_response": self.raw_ai_response,
            "output_report": self.output_report.to_dict() if self.output_report else None,
            "final_output": self.final_output,
        }
