"""Vector database manager supporting ChromaDB and in-memory cosine similarity search."""

import os
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from app.config import settings
from app.rag.ingestion import DocumentChunk
from app.rag.embeddings import embedding_engine

logger = logging.getLogger("ai_assistant.vector_store")


class VectorStore:
    """Vector database interface with ChromaDB persistence and in-memory fallback."""

    def __init__(
        self,
        collection_name: str = "knowledge_base",
        persist_directory: str = settings.CHROMA_PERSIST_DIRECTORY
    ):
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self._chroma_client = None
        self._collection = None
        self._in_memory_docs: List[DocumentChunk] = []
        self._in_memory_embeddings: List[List[float]] = []
        self._init_store()

    def _init_store(self):
        """Initialize ChromaDB or fallback to in-memory store."""
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            
            os.makedirs(self.persist_directory, exist_ok=True)
            self._chroma_client = chromadb.PersistentClient(path=self.persist_directory)
            self._collection = self._chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"ChromaDB initialized at {self.persist_directory} [Collection: {self.collection_name}]")
        except Exception as e:
            logger.warning(f"ChromaDB initialization failed ({e}). Using robust In-Memory Vector Store.")
            self._chroma_client = None
            self._collection = None

    def add_chunks(self, chunks: List[DocumentChunk]):
        """Embed and insert document chunks into the vector store."""
        if not chunks:
            return

        texts = [c.text for c in chunks]
        embeddings = embedding_engine.embed_texts(texts)

        if self._collection is not None:
            self._collection.add(
                ids=[c.chunk_id for c in chunks],
                embeddings=embeddings,
                documents=texts,
                metadatas=[c.metadata for c in chunks]
            )
        else:
            self._in_memory_docs.extend(chunks)
            self._in_memory_embeddings.extend(embeddings)

        logger.info(f"Successfully added {len(chunks)} chunks to vector store.")

    def search(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Query vector database for most semantically similar chunks."""
        query_embedding = embedding_engine.embed_query(query)

        if self._collection is not None:
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, self._collection.count() or 1),
                include=["documents", "metadatas", "distances"]
            )
            hits = []
            if results and results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    doc_id = results["ids"][0][i]
                    text = results["documents"][0][i]
                    metadata = results["metadatas"][0][i]
                    distance = results["distances"][0][i] if "distances" in results else 0.0
                    similarity = 1.0 - float(distance) if distance is not None else 1.0
                    hits.append({
                        "chunk_id": doc_id,
                        "text": text,
                        "metadata": metadata,
                        "score": round(max(0.0, min(1.0, similarity)), 4)
                    })
            return hits

        # In-Memory Cosine Similarity
        if not self._in_memory_embeddings:
            return []

        q_vec = np.array(query_embedding, dtype=np.float32)
        matrix = np.array(self._in_memory_embeddings, dtype=np.float32)
        
        # Dot product of normalized vectors
        scores = np.dot(matrix, q_vec)
        top_indices = np.argsort(scores)[::-1][:top_k]

        hits = []
        for idx in top_indices:
            chunk = self._in_memory_docs[idx]
            score = float(scores[idx])
            hits.append({
                "chunk_id": chunk.chunk_id,
                "text": chunk.text,
                "metadata": chunk.metadata,
                "score": round(max(0.0, min(1.0, score)), 4)
            })

        return hits

    def count(self) -> int:
        """Return total number of chunks stored."""
        if self._collection is not None:
            return self._collection.count()
        return len(self._in_memory_docs)

    def clear(self):
        """Clear the vector database."""
        if self._collection is not None and self._chroma_client is not None:
            self._chroma_client.delete_collection(self.collection_name)
            self._collection = self._chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        self._in_memory_docs.clear()
        self._in_memory_embeddings.clear()


# Global vector store instance
vector_store = VectorStore()
