"""Document ingestion, preprocessing, and recursive text chunking."""

import os
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.config import settings


class DocumentChunk(BaseModel):
    """Representing an individual text chunk with metadata."""
    chunk_id: str
    doc_id: str
    text: str
    metadata: Dict[str, Any]


class DocumentChunker:
    """Recursive text chunker preserving sentence and paragraph integrity."""

    def __init__(
        self,
        chunk_size: int = settings.CHUNK_SIZE,
        chunk_overlap: int = settings.CHUNK_OVERLAP,
        separators: Optional[List[str]] = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", "! ", "? ", "; ", " ", ""]

    def chunk_text(self, text: str, doc_id: str, metadata: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        """Split text into overlapping chunks recursively based on separators."""
        cleaned_text = re.sub(r"\r\n", "\n", text).strip()
        if not cleaned_text:
            return []

        raw_chunks = self._recursive_split(cleaned_text, self.separators)
        
        # Merge small slices up to chunk_size with overlap
        merged_chunks = []
        current_chunk = ""

        for piece in raw_chunks:
            if not piece.strip():
                continue
            if len(current_chunk) + len(piece) <= self.chunk_size:
                current_chunk += piece
            else:
                if current_chunk.strip():
                    merged_chunks.append(current_chunk.strip())
                # Keep overlap from the end of current_chunk
                if self.chunk_overlap > 0 and len(current_chunk) > self.chunk_overlap:
                    current_chunk = current_chunk[-self.chunk_overlap:] + piece
                else:
                    current_chunk = piece

        if current_chunk.strip():
            merged_chunks.append(current_chunk.strip())

        meta = metadata or {}
        chunks: List[DocumentChunk] = []
        for idx, chunk_text in enumerate(merged_chunks):
            chunk_id = f"{doc_id}_chunk_{idx}"
            chunk_meta = {**meta, "chunk_index": idx, "total_chunks": len(merged_chunks)}
            chunks.append(DocumentChunk(
                chunk_id=chunk_id,
                doc_id=doc_id,
                text=chunk_text,
                metadata=chunk_meta
            ))

        return chunks

    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        """Internal recursive splitter using hierarchy of separators."""
        final_splits = []
        separator = separators[-1]
        for s in separators:
            if s == "" or s in text:
                separator = s
                break

        splits = text.split(separator) if separator != "" else list(text)
        for s in splits:
            if not s:
                continue
            item = s if separator == "" else s + separator
            if len(item) <= self.chunk_size or len(separators) <= 1:
                final_splits.append(item)
            else:
                final_splits.extend(self._recursive_split(item, separators[1:]))

        return final_splits


# Global chunker instance
chunker = DocumentChunker()
