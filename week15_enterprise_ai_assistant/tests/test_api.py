"""Integration and endpoint tests for FastAPI server and resilience mechanisms."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.cache import cache
from app.core.resilience import rate_limiter

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "primary_provider" in data


def test_metrics_endpoint():
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "cache_stats" in data
    assert "vector_store_count" in data


def test_chat_endpoint_mock():
    payload = {
        "message": "Calculate what is 15 * 12",
        "provider": "mock",
        "enable_rag": True,
        "enable_tools": True,
        "use_cache": False
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "latency_ms" in data
    assert "provider_used" in data
    assert len(data["tools_used"]) >= 1


def test_response_caching():
    cache.clear()
    payload = {
        "message": "Explain quantum entanglement in simple terms",
        "provider": "mock",
        "enable_rag": False,
        "enable_tools": False,
        "use_cache": True
    }
    # First call: cache miss
    resp1 = client.post("/api/chat", json=payload)
    assert resp1.status_code == 200
    assert resp1.json()["cached"] is False

    # Second call: cache hit
    resp2 = client.post("/api/chat", json=payload)
    assert resp2.status_code == 200
    assert resp2.json()["cached"] is True


def test_rag_ingest_and_search_endpoints():
    ingest_payload = {
        "document_id": "test_ingest_doc",
        "text": "Vector embeddings represent text semantics in multi-dimensional space.",
        "metadata": {"topic": "ai"}
    }
    resp = client.post("/api/rag/ingest", json=ingest_payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"

    search_resp = client.post("/api/rag/search", json={"query": "embeddings semantics", "top_k": 2})
    assert search_resp.status_code == 200
    results = search_resp.json()["results"]
    assert len(results) > 0


def test_structured_extraction():
    text_content = "Antigravity IDE is released by the Deepmind team. It delivers high agentic efficiency and received positive community reception."
    resp = client.post("/api/extract", data={"text": text_content})
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert "key_points" in data
    assert isinstance(data["key_points"], list)
