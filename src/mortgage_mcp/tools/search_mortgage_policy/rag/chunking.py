"""
MCP references: search_mortgage_policy
Purpose: Splits policy text into retrieval chunks with stable IDs for citation tracking.
"""

from __future__ import annotations

import hashlib


def chunk_text(text: str, *, max_chars: int = 420, overlap: int = 60) -> list[str]:
    """Simple length-based chunking with overlap (mock enterprise RAG baseline)."""
    text = text.strip()
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks


def stable_chunk_id(document_id: str, chunk_index: int, content: str) -> str:
    digest = hashlib.sha256(f"{document_id}:{chunk_index}:{content}".encode()).hexdigest()[:10]
    return f"CHUNK-{document_id.split('-')[1] if '-' in document_id else 'DOC'}-{digest.upper()}"
