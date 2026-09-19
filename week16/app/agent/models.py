"""Pydantic models for Agentic Workflow, Trajectory, and Multi-Agent Verification.

Features resilient fallback to Python dataclasses if running in a lightweight environment without Pydantic.
"""

from typing import List, Dict, Any, Optional

try:
    from pydantic import BaseModel, Field
except ImportError:
    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        def dict(self, *args, **kwargs):
            return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
        def model_dump(self, *args, **kwargs):
            return self.dict()
        def __repr__(self):
            return f"{self.__class__.__name__}({self.__dict__})"

    def Field(default=None, default_factory=None, **kwargs):
        if default_factory is not None:
            return default_factory()
        return default


class AgentAction(BaseModel):
    """Action selected by the agent."""
    tool_name: str = Field(..., description="Name of the tool to execute")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments for the tool")

    def __init__(self, **kwargs):
        if "arguments" not in kwargs or kwargs["arguments"] is None:
            kwargs["arguments"] = {}
        super().__init__(**kwargs)


class AgentStep(BaseModel):
    """Single step in an agent's reasoning-action trajectory."""
    step_number: int = Field(default=1)
    thought: str = Field(default="", description="Internal reasoning and evaluation of current state")
    action: Optional[AgentAction] = Field(default=None, description="Action taken, or None if finishing")
    observation: Optional[str] = Field(default=None, description="Raw observation from environment or tool")
    compacted_observation: Optional[str] = Field(default=None, description="Compacted context-engineered observation")
    prompt_tokens: int = Field(default=0)
    completion_tokens: int = Field(default=0)
    latency_ms: float = Field(default=0.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class AgentScratchpad(BaseModel):
    """Structured external memory tracking facts and objectives across iterations."""
    original_goal: str = Field(default="")
    verified_facts: List[str] = Field(default_factory=list)
    pending_checks: List[str] = Field(default_factory=list)
    contradictions_detected: List[str] = Field(default_factory=list)

    def __init__(self, **kwargs):
        if "verified_facts" not in kwargs:
            kwargs["verified_facts"] = []
        if "pending_checks" not in kwargs:
            kwargs["pending_checks"] = []
        if "contradictions_detected" not in kwargs:
            kwargs["contradictions_detected"] = []
        super().__init__(**kwargs)

    def to_context_string(self) -> str:
        facts_str = "\n".join(f"- {f}" for f in self.verified_facts) if self.verified_facts else "(No verified facts yet)"
        pending_str = "\n".join(f"- {p}" for p in self.pending_checks) if self.pending_checks else "(None)"
        return (
            f"=== AGENT SCRATCHPAD ===\n"
            f"Goal: {self.original_goal}\n"
            f"Verified Facts:\n{facts_str}\n"
            f"Pending Verifications:\n{pending_str}\n"
            f"========================"
        )


class VerificationResult(BaseModel):
    """Critique and factuality evaluation from Verifier agent."""
    passed: bool = Field(default=True, description="Whether the answer is factual, complete, and verified")
    score: float = Field(default=0.9, description="Confidence/factuality score")
    critique: str = Field(default="", description="Detailed feedback or justification")
    unsupported_claims: List[str] = Field(default_factory=list, description="Claims lacking citation or proof")
    recommended_action: str = Field(default="accept", description="'accept', 'search_again', or 'recalculate'")

    def __init__(self, **kwargs):
        if "unsupported_claims" not in kwargs:
            kwargs["unsupported_claims"] = []
        super().__init__(**kwargs)


class AgentTrajectory(BaseModel):
    """Full execution trajectory across iterations with token and performance accounting."""
    steps: List[AgentStep] = Field(default_factory=list)
    total_steps: int = Field(default=0)
    total_prompt_tokens: int = Field(default=0)
    total_completion_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)
    estimated_cost_usd: float = Field(default=0.0)
    stop_reason: str = Field(default="completed")
    total_latency_ms: float = Field(default=0.0)

    def __init__(self, **kwargs):
        if "steps" not in kwargs:
            kwargs["steps"] = []
        super().__init__(**kwargs)


class AgentResponse(BaseModel):
    """Unified structured response returned by the Agentic Assistant."""
    answer: str = Field(default="")
    mode: str = Field(default="single_agent", description="'single_agent' or 'multi_agent'")
    trajectory: Optional[AgentTrajectory] = Field(default=None)
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    verification: Optional[VerificationResult] = Field(default=None)
    confidence_score: float = Field(default=0.9)
    clarification_question: Optional[str] = Field(default=None)

    def __init__(self, **kwargs):
        if "citations" not in kwargs:
            kwargs["citations"] = []
        super().__init__(**kwargs)
