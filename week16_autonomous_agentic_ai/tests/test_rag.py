"""Unit tests for RAG pipeline: chunking, embeddings, and vector store."""

import pytest
from app.rag.ingestion import DocumentChunker
from app.rag.embeddings import embedding_engine
from app.rag.vector_store import VectorStore


def test_document_chunker():
    chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
    text = (
        "Retrieval-Augmented Generation enhances large language models by pulling relevant external context. "
        "Dense embeddings map text into continuous mathematical spaces. "
        "Vector databases index these dense embeddings using cosine similarity algorithms."
    )
    chunks = chunker.chunk_text(text, doc_id="test_doc_1", metadata={"author": "test"})
    assert len(chunks) >= 2
    assert chunks[0].doc_id == "test_doc_1"
    assert chunks[0].metadata["author"] == "test"
    assert len(chunks[0].text) > 0


def test_embedding_generation():
    texts = ["Artificial intelligence is transforming software engineering.", "Vector databases allow fast nearest-neighbor search."]
    embeddings = embedding_engine.embed_texts(texts)
    assert len(embeddings) == 2
    assert len(embeddings[0]) > 0
    assert isinstance(embeddings[0][0], float)

    query_vec = embedding_engine.embed_query("AI systems")
    assert len(query_vec) == len(embeddings[0])


def test_vector_store_indexing_and_search():
    store = VectorStore(collection_name="test_collection_mem", persist_directory="./data/test_chroma")
    store.clear()

    chunker = DocumentChunker(chunk_size=200, chunk_overlap=30)
    doc_text = "FastAPI is a modern asynchronous web framework for Python. ChromaDB is an open-source vector database."
    chunks = chunker.chunk_text(doc_text, doc_id="doc_fastapi")
    
    store.add_chunks(chunks)
    assert store.count() > 0

    results = store.search("Tell me about FastAPI framework", top_k=2)
    assert len(results) > 0
    assert "FastAPI" in results[0]["text"]
    assert results[0]["score"] >= 0.0

    store.clear()
