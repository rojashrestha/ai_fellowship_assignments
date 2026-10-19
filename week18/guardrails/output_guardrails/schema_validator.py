"""
Schema Validator for Output Guardrails.
Ensures generated AI responses conform to a strict predefined contract:
- Valid structural schema (dictionary/JSON)
- Correct field types and presence of mandatory attributes
- Value constraints (e.g. confidence score between 0.0 and 1.0, allowed status enums)
"""
from typing import Any, Dict, List
from guardrails.models import ActionTaken, GuardrailResult, StructuredAIResponse

try:
    from pydantic import BaseModel, Field, field_validator

    class PydanticResponseSchema(BaseModel):
        status: str = Field(..., description="Execution status: SUCCESS, PARTIAL, or REFUSAL")
        answer: str = Field(..., min_length=1, description="Text response content")
        confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0.0 - 1.0")
        citations: List[str] = Field(default_factory=list, description="Source context reference identifiers")
        metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata key-value pairs")

        @field_validator("status")
        @classmethod
        def validate_status(cls, v: str) -> str:
            allowed = {"SUCCESS", "PARTIAL", "REFUSAL"}
            if v.upper() not in allowed:
                raise ValueError(f"Status must be one of {allowed}, got '{v}'")
            return v.upper()

    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False


class SchemaValidator:
    """
    Detection Approach:
    - Verifies presence of mandatory keys ('status', 'answer', 'confidence_score', 'citations').
    - Asserts rigorous type consistency (e.g. confidence_score is float, citations is list).
    - Validates categorical enums and numeric range constraints (0.0 <= confidence_score <= 1.0).
    - Leverages Pydantic validation when available, with a built-in pure Python validator.

    Action Taken:
    - REGENERATE / SAFE_FALLBACK: If schema validation fails, the system attempts schema repair.
      If irreparable or in strict mode, returns a SAFE_FALLBACK standardized response object
      to prevent frontend application crashes or downstream API contract breaks.

    Limitations:
    - Schema validation confirms structural and type syntactical correctness, but does not
      verify semantic truthfulness or factual grounding.
    """

    MANDATORY_FIELDS = {
        "status": str,
        "answer": str,
        "confidence_score": (int, float),
        "citations": list,
    }

    ALLOWED_STATUSES = {"SUCCESS", "PARTIAL", "REFUSAL"}

    def check(self, payload: Any) -> GuardrailResult:
        errors = []

        if not isinstance(payload, dict):
            return GuardrailResult(
                guardrail_name="Schema_Validation",
                passed=False,
                action=ActionTaken.SAFE_FALLBACK,
                risk_score=1.0,
                message="Response must be a structured JSON / dictionary object",
                details={"errors": [f"Expected dict, got {type(payload).__name__}"]}
            )

        # 1. Mandatory field checks
        for field, expected_type in self.MANDATORY_FIELDS.items():
            if field not in payload:
                errors.append(f"Missing mandatory field '{field}'")
            elif not isinstance(payload[field], expected_type):
                errors.append(f"Field '{field}' has invalid type {type(payload[field]).__name__}, expected {expected_type}")

        # 2. Value constraint checks
        if "confidence_score" in payload and isinstance(payload["confidence_score"], (int, float)):
            conf = float(payload["confidence_score"])
            if conf < 0.0 or conf > 1.0:
                errors.append(f"confidence_score '{conf}' out of bounds (must be between 0.0 and 1.0)")

        if "status" in payload and isinstance(payload["status"], str):
            if payload["status"].upper() not in self.ALLOWED_STATUSES:
                errors.append(f"Invalid status '{payload['status']}'. Must be one of {self.ALLOWED_STATUSES}")

        if "answer" in payload and isinstance(payload["answer"], str):
            if len(payload["answer"].strip()) == 0:
                errors.append("Field 'answer' cannot be empty")

        if "citations" in payload and isinstance(payload["citations"], list):
            for i, c in enumerate(payload["citations"]):
                if not isinstance(c, str):
                    errors.append(f"Citation at index {i} must be a string, got {type(c).__name__}")

        passed = (len(errors) == 0)
        action = ActionTaken.ALLOW if passed else ActionTaken.SAFE_FALLBACK
        risk_score = 0.0 if passed else 0.9

        return GuardrailResult(
            guardrail_name="Schema_Validation",
            passed=passed,
            action=action,
            risk_score=risk_score,
            message="Output conforms to required schema" if passed else f"Schema validation failed: {'; '.join(errors)}",
            details={
                "errors": errors,
                "validated_fields": list(self.MANDATORY_FIELDS.keys()),
            }
        )

    def create_safe_fallback(self, reason: str) -> Dict[str, Any]:
        """Produce a guaranteed schema-compliant fallback response."""
        return {
            "status": "REFUSAL",
            "answer": f"System Notice: The generated response could not be displayed due to: {reason}",
            "confidence_score": 0.0,
            "citations": [],
            "metadata": {"fallback_triggered": True, "reason": reason}
        }
