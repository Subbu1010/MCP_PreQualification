"""
MCP references: search_mortgage_policy
Purpose: Deterministic embedding fallback when Google embedding API is unavailable (offline dev / tests).
"""

from __future__ import annotations

import hashlib
from typing import Final

import numpy as np

_DIM: Final[int] = 256


def hash_embed(text: str, dim: int = _DIM) -> np.ndarray:
    """
    Maps arbitrary text to a L2-normalized float32 vector using repeated SHA-256 expansion.

    This is not a semantic embedding model; it exists so FAISS retrieval works without cloud keys.
    """
    raw = text.encode("utf-8")
    buf = bytearray()
    counter = 0
    while len(buf) < dim * 4:
        buf.extend(hashlib.sha256(raw + str(counter).encode()).digest())
        counter += 1
    vec = np.frombuffer(buf[: dim * 4], dtype=np.uint32).astype(np.float32)
    vec = vec / (np.linalg.norm(vec) + 1e-8)
    return vec
