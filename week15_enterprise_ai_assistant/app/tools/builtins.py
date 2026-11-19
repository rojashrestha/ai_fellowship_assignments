"""Built-in tool implementations for tool calling."""

import math
import datetime
from typing import Dict, Any, List
from app.rag.vector_store import vector_store


def calculate(expression: str) -> Dict[str, Any]:
    """
    Safely evaluate a mathematical expression.
    Supported operations: +, -, *, /, **, %, sqrt, sin, cos, tan, log, exp, pi, e.
    """
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
        # Sanitization check
        cleaned = expression.strip()
        if any(char in cleaned for char in [";", "__", "import", "exec", "eval", "os", "sys"]):
            return {"error": "Invalid characters in mathematical expression"}
        
        result = eval(cleaned, {"__builtins__": {}}, safe_dict)
        return {"expression": expression, "result": result, "status": "success"}
    except Exception as e:
        return {"expression": expression, "error": str(e), "status": "failed"}


def get_current_datetime(timezone_offset_hours: float = 0.0) -> Dict[str, Any]:
    """Get the current UTC or offset date and time."""
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
    q_lower = query.lower()
    mock_knowledge = [
        {"title": "FastAPI Framework", "snippet": "FastAPI is a modern, fast web framework for building APIs with Python 3.8+ based on standard Python type hints."},
        {"title": "vLLM High-Throughput Serving", "snippet": "vLLM is an easy, fast, and cheap LLM serving engine with PagedAttention and continuous batching."},
        {"title": "RAG Architectures", "snippet": "Retrieval-Augmented Generation enhances LLM responses by retrieving relevant context chunks from dense vector embeddings."},
        {"title": "ONNX Runtime", "snippet": "ONNX Runtime is a cross-platform inference and training machine-learning accelerator compatible with PyTorch and TensorFlow."}
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
    hits = vector_store.search(query, top_k=top_k)
    return {
        "query": query,
        "num_results": len(hits),
        "results": hits,
        "status": "success"
    }
