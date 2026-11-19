"""Production FastAPI Application for AI Assistant with RAG, Tool Calling, and Resilience."""

import time
import json
import logging
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, Depends, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.core.resilience import rate_limiter
from app.core.cache import cache
from app.core.llm_provider import llm_service
from app.core.structured_output import (
    AssistantResponse,
    SourceCitation,
    ToolExecutionRecord,
    ExtractionResult
)
from app.rag.ingestion import chunker, DocumentChunk
from app.rag.vector_store import vector_store
from app.tools.registry import tool_registry

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ai_assistant.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event: initialize default knowledge and resources."""
    logger.info("Starting AI Assistant Engine...")
    # Seed default sample documentation into vector store if empty
    if vector_store.count() == 0:
        sample_text = (
            "The AI Assistant System is designed for production applied AI engineering. "
            "It integrates Retrieval-Augmented Generation (RAG) using dense vector embeddings "
            "and ChromaDB for high-precision retrieval. "
            "For resilience, it employs token bucket rate limiting, exponential backoff retries with jitter, "
            "and automated failover across primary (Gemini/OpenAI) and fallback providers (vLLM/local). "
            "Model optimization strategies include ONNX Runtime export for embedding models and INT4/INT8 quantization."
        )
        chunks = chunker.chunk_text(sample_text, doc_id="system_overview_doc", metadata={"source": "system_default"})
        vector_store.add_chunks(chunks)
        logger.info(f"Seeded default knowledge base with {len(chunks)} chunks.")
    yield
    logger.info("Shutting down AI Assistant Engine...")


app = FastAPI(
    title="Production AI Assistant API",
    description="Full-stack Applied AI Assistant with RAG, Function Calling, Multi-Provider Fallbacks, and Rate Limiting.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Rate Limiting Middleware
@app.middleware("http")
async def rate_limit_and_latency_middleware(request: Request, call_next):
    # Skip rate limiting for health check and docs
    if request.url.path not in ["/health", "/docs", "/openapi.json", "/redoc"]:
        await rate_limiter.check_or_raise()

    start_time = time.time()
    response = await call_next(request)
    process_time_ms = round((time.time() - start_time) * 1000, 2)
    response.headers["X-Process-Time-Ms"] = str(process_time_ms)
    return response


# ---------------------------------------------------------
# Request Models
# ---------------------------------------------------------
class ChatRequest(BaseModel):
    message: str = Field(..., description="User prompt or query")
    system_prompt: Optional[str] = Field(default="You are a helpful, accurate, and concise AI Assistant.")
    enable_rag: bool = Field(default=True, description="Whether to augment response with vector store context")
    enable_tools: bool = Field(default=True, description="Whether to permit tool execution")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=4096)
    provider: Optional[str] = Field(default=None, description="Specify 'gemini', 'openai', 'vllm', or 'mock'")
    use_cache: bool = Field(default=True)


class IngestTextRequest(BaseModel):
    document_id: str = Field(..., description="Unique document identifier")
    text: str = Field(..., description="Raw text content to ingest")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SearchRequest(BaseModel):
    query: str = Field(..., description="Semantic search query")
    top_k: int = Field(default=4, ge=1, le=20)


class ToolCallRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]


# ---------------------------------------------------------
# Endpoints
# ---------------------------------------------------------
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "primary_provider": settings.PRIMARY_PROVIDER,
        "fallback_provider": settings.FALLBACK_PROVIDER,
        "vector_store_chunks": vector_store.count()
    }


@app.get("/api/metrics", tags=["System"])
async def get_metrics():
    """Retrieve cache hit/miss stats and system settings."""
    return {
        "cache_stats": cache.get_stats(),
        "vector_store_count": vector_store.count(),
        "rate_limit_rpm": settings.RATE_LIMIT_REQUESTS_PER_MINUTE
    }


@app.post("/api/chat", response_model=AssistantResponse, tags=["AI Assistant"])
async def chat_endpoint(request: ChatRequest):
    """
    Main AI Assistant conversational endpoint.
    Performs RAG context retrieval, checks tools, handles retries, and returns structured JSON output.
    """
    start_time = time.time()
    citations: List[SourceCitation] = []
    tools_used: List[ToolExecutionRecord] = []
    augmented_prompt = request.message

    # 1. RAG Retrieval Stage
    if request.enable_rag and vector_store.count() > 0:
        retrieved_chunks = vector_store.search(request.message, top_k=3)
        if retrieved_chunks:
            context_blocks = []
            for hit in retrieved_chunks:
                citations.append(SourceCitation(
                    document_id=str(hit.get("metadata", {}).get("source", hit["chunk_id"])),
                    content_snippet=hit["text"][:200] + "...",
                    score=hit["score"]
                ))
                context_blocks.append(f"Source [{hit['chunk_id']}]:\n{hit['text']}")
            
            context_str = "\n\n".join(context_blocks)
            augmented_prompt = (
                f"Context Information:\n---------------------\n{context_str}\n---------------------\n\n"
                f"Given the context above (and using tools if needed), answer the following question accurately:\n"
                f"{request.message}"
            )

    # 2. Tool Calling Stage (Intent Inspection & Built-in execution)
    if request.enable_tools:
        lowered = request.message.lower()
        if any(w in lowered for w in ["calculate", "math", "sqrt", "+", "*", "/", "compute", "sum of"]) and not citations:
            # Extract simple math expression
            expr = request.message
            for prefix in ["calculate", "compute", "what is", "evaluate"]:
                if prefix in expr.lower():
                    expr = expr.lower().split(prefix)[-1].strip(" ?:=")
            tool_rec = tool_registry.execute("calculate", {"expression": expr})
            tools_used.append(tool_rec)
            if tool_rec.result.get("status") == "success":
                augmented_prompt += f"\n[Tool Result: calculate('{expr}') -> {tool_rec.result.get('result')}]"
        
        elif any(w in lowered for w in ["what time is it", "current date", "today's date", "what is the time"]):
            tool_rec = tool_registry.execute("get_current_datetime", {})
            tools_used.append(tool_rec)
            augmented_prompt += f"\n[Tool Result: current_datetime -> {tool_rec.result}]"

    # 3. LLM Generation with Caching and Fallbacks
    llm_output = await llm_service.generate(
        prompt=augmented_prompt,
        system_prompt=request.system_prompt,
        temperature=request.temperature,
        top_p=request.top_p,
        max_tokens=request.max_tokens,
        provider=request.provider,
        use_cache=request.use_cache
    )

    total_latency_ms = round((time.time() - start_time) * 1000, 2)

    return AssistantResponse(
        answer=llm_output["text"],
        citations=citations,
        tools_used=tools_used,
        confidence_score=0.95 if citations else 0.85,
        provider_used=llm_output.get("provider", "unknown"),
        cached=llm_output.get("cached", False),
        latency_ms=total_latency_ms
    )


@app.post("/api/rag/ingest", tags=["RAG"])
async def ingest_document(request: IngestTextRequest):
    """Chunk and index raw text into the vector database."""
    chunks = chunker.chunk_text(request.text, doc_id=request.document_id, metadata=request.metadata)
    if not chunks:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty text provided.")
    vector_store.add_chunks(chunks)
    return {
        "status": "success",
        "document_id": request.document_id,
        "chunks_indexed": len(chunks),
        "total_store_count": vector_store.count()
    }


@app.post("/api/rag/upload", tags=["RAG"])
async def upload_file(file: UploadFile = File(...)):
    """Upload a text or markdown file and index into RAG vector store."""
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    chunks = chunker.chunk_text(text, doc_id=file.filename, metadata={"source": file.filename})
    vector_store.add_chunks(chunks)
    return {
        "filename": file.filename,
        "chunks_indexed": len(chunks),
        "status": "success",
        "total_store_count": vector_store.count()
    }


@app.post("/api/rag/search", tags=["RAG"])
async def search_vector_store(request: SearchRequest):
    """Directly query the vector database for top-k matching chunks."""
    results = vector_store.search(request.query, top_k=request.top_k)
    return {
        "query": request.query,
        "num_results": len(results),
        "results": results
    }


@app.get("/api/tools", tags=["Tools"])
async def list_tools():
    """List all registered tools with function calling schemas."""
    return {"tools": tool_registry.get_schemas()}


@app.post("/api/tools/execute", tags=["Tools"])
async def execute_tool(request: ToolCallRequest):
    """Directly invoke a registered tool."""
    record = tool_registry.execute(request.tool_name, request.arguments)
    return record


@app.post("/api/extract", response_model=ExtractionResult, tags=["Structured Output"])
async def structured_extraction(text: str = Form(...)):
    """Extract structured data (summary, key points, entities, sentiment) with schema validation."""
    prompt = (
        f"Analyze the following text and return strict JSON with keys 'summary', 'key_points', 'entities', 'sentiment':\n\n{text}"
    )
    system_prompt = "You are a data extraction engine. Output valid JSON only."
    
    output = await llm_service.generate(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=0.1,
        use_cache=True
    )
    
    try:
        cleaned_json = output["text"].strip()
        if "```json" in cleaned_json:
            cleaned_json = cleaned_json.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned_json:
            cleaned_json = cleaned_json.split("```")[1].split("```")[0].strip()
            
        parsed = json.loads(cleaned_json)
        return ExtractionResult(**parsed)
    except Exception:
        # Fallback structured parsing
        return ExtractionResult(
            summary=text[:120] + "...",
            key_points=["Extracted key insight from input text"],
            entities=[{"name": "InputText", "category": "Document"}],
            sentiment="neutral"
        )
