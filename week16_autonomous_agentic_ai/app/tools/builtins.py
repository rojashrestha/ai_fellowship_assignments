"""Built-in tool implementations for tool calling with Failure Injection support."""

import math
import datetime
import logging
from typing import Dict, Any, List, Optional
from app.rag.vector_store import vector_store
from app.agent.skills import skill_registry

logger = logging.getLogger("ai_assistant.tools")


class FailureInjectionState:
    """Manages active failure modes for testing system resilience."""
    active_failure_mode: Optional[str] = None  # "tool_unavailable", "malformed_output", "timeout"
    target_tool: Optional[str] = None  # None means applies to any tool requested

    @classmethod
    def set_failure(cls, mode: Optional[str], target_tool: Optional[str] = None):
        cls.active_failure_mode = mode
        cls.target_tool = target_tool

    @classmethod
    def check_failure(cls, tool_name: str):
        if not cls.active_failure_mode:
            return
        if cls.target_tool and cls.target_tool != tool_name:
            return

        mode = cls.active_failure_mode
        if mode == "tool_unavailable":
            raise RuntimeError(f"ServiceUnavailableError 503: Tool '{tool_name}' backend endpoint is temporarily offline.")
        elif mode == "timeout":
            raise TimeoutError(f"GatewayTimeoutError 504: Execution of tool '{tool_name}' timed out after 10000ms.")
        elif mode == "malformed_output":
            return {"_corrupt_raw_bytes": "0xDEADBEEF!!MalformedBinaryCorruptedPayload", "status": "corrupt"}


def calculate(expression: str) -> Dict[str, Any]:
    """
    Safely evaluate a mathematical expression.
    Supported operations: +, -, *, /, **, %, sqrt, sin, cos, tan, log, exp, pi, e.
    """
    FailureInjectionState.check_failure("calculate")

    safe_dict = {
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "exp": math.exp,
        "pi": math.pi,
        "e": math.e,
        "pow": pow,
        "abs": abs,
        "round": round
    }
    try:
        cleaned = expression.strip()
        if any(char in cleaned for char in [";", "__", "import", "exec", "eval", "os", "sys"]):
            return {"error": "Invalid characters in mathematical expression", "status": "failed"}
        
        result = eval(cleaned, {"__builtins__": {}}, safe_dict)
        return {"expression": expression, "result": result, "status": "success"}
    except Exception as e:
        return {"expression": expression, "error": str(e), "status": "failed"}


def get_current_datetime(timezone_offset_hours: float = 0.0) -> Dict[str, Any]:
    """Get the current UTC or offset date and time."""
    FailureInjectionState.check_failure("get_current_datetime")

    tz = datetime.timezone(datetime.timedelta(hours=timezone_offset_hours))
    now = datetime.datetime.now(tz)
    return {
        "iso_format": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "day_of_week": now.strftime("%A"),
        "status": "success"
    }


def search_web(query: str) -> Dict[str, Any]:
    """
    Simulated live web search returning relevant snippets for a query.
    """
    corrupt = FailureInjectionState.check_failure("search_web")
    if corrupt:
        return corrupt

    q_lower = query.lower()
    mock_knowledge = [
        {"title": "FastAPI Framework", "snippet": "FastAPI is a modern, fast web framework for building APIs with Python 3.8+ based on standard Python type hints."},
        {"title": "vLLM High-Throughput Serving", "snippet": "vLLM is an easy, fast, and cheap LLM serving engine with PagedAttention and continuous batching."},
        {"title": "RAG Architectures", "snippet": "Retrieval-Augmented Generation enhances LLM responses by retrieving relevant context chunks from dense vector embeddings."},
        {"title": "ONNX Runtime", "snippet": "ONNX Runtime is a cross-platform inference and training machine-learning accelerator compatible with PyTorch and TensorFlow."},
        {"title": "Agentic Design Patterns", "snippet": "Agentic loops allow dynamic multi-step planning, reflection, and tool execution with iterative context management."},
        {"title": "AI Fellowship Guidelines", "snippet": "The AI Fellowship Week 16 requires implementing agentic loops, context compaction, and custom evaluation harnesses."}
    ]
    
    matches = [k for k in mock_knowledge if any(word in k["title"].lower() or word in k["snippet"].lower() for word in q_lower.split())]
    if not matches:
        matches = mock_knowledge[:2]

    return {
        "query": query,
        "results": matches,
        "status": "success"
    }


def query_knowledge_base(query: str, top_k: int = 3) -> Dict[str, Any]:
    """Search the internal vector database for relevant documentation chunks."""
    corrupt = FailureInjectionState.check_failure("query_knowledge_base")
    if corrupt:
        return corrupt

    hits = vector_store.search(query, top_k=top_k)
    return {
        "query": query,
        "num_results": len(hits),
        "results": hits,
        "status": "success"
    }


def load_skill_instructions(skill_name: str) -> Dict[str, Any]:
    """Load detailed instructions for a skill using Progressive Disclosure context engineering."""
    content = skill_registry.load_full_skill(skill_name)
    return {
        "skill_name": skill_name,
        "instructions": content,
        "status": "success"
    }
