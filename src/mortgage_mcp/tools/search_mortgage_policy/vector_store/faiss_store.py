"""
MCP references: search_mortgage_policy
Purpose: Thin wrapper around a FAISS inner-product index for normalized chunk embeddings.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import faiss
import numpy as np


@dataclass
class PolicyIndex:
    """In-memory FAISS index plus aligned chunk metadata (owned by policy search tool only)."""

    index: faiss.IndexFlatIP
    chunks: list[dict[str, Any]]
    dim: int

    def search(self, query_vector: np.ndarray, *, top_k: int) -> list[tuple[float, dict[str, Any]]]:
        q = query_vector.astype("float32").reshape(1, -1)
        if q.shape[1] != self.dim:
            raise ValueError(f"Query dim {q.shape[1]} != index dim {self.dim}")
        faiss.normalize_L2(q)
        scores, ids = self.index.search(q, top_k)
        hits: list[tuple[float, dict[str, Any]]] = []
        for score, idx in zip(scores[0], ids[0]):
            if int(idx) < 0:
                continue
            hits.append((float(score), self.chunks[int(idx)]))
        return hits


def build_ip_index(vectors: np.ndarray, chunks: list[dict[str, Any]]) -> PolicyIndex:
    """Vectors must be float32 row matrix; rows are L2-normalized before indexing."""
    mat = vectors.astype("float32", copy=False)
    faiss.normalize_L2(mat)
    dim = mat.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(mat)
    return PolicyIndex(index=index, chunks=chunks, dim=dim)
