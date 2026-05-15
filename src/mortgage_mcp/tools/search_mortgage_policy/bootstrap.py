"""
MCP references: search_mortgage_policy
Purpose: Builds (or rebuilds) the in-memory FAISS policy index from this tool's local policy_documents/.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Final

import numpy as np

from mortgage_mcp.common.settings import get_settings
from mortgage_mcp.tools.search_mortgage_policy.embeddings.google_embeddings import google_embed_text
from mortgage_mcp.tools.search_mortgage_policy.embeddings.hash_embedding import hash_embed
from mortgage_mcp.tools.search_mortgage_policy.rag.chunking import chunk_text, stable_chunk_id
from mortgage_mcp.tools.search_mortgage_policy.vector_store.faiss_store import PolicyIndex, build_ip_index

logger = logging.getLogger(__name__)

_INDEX: PolicyIndex | None = None
_EMBED_MODE: str = "hash"
_INDEX_VERSION: Final[str] = "faiss-policy-v20260514"


def tool_root() -> Path:
    return Path(__file__).resolve().parent


def data_dir() -> Path:
    return tool_root() / "data"


async def embed_query(text: str) -> np.ndarray:
    """Embeds text using the strategy selected in `_detect_embed_mode()` (must match index build)."""
    if _EMBED_MODE == "google":
        vec = await google_embed_text(text)
        if vec is None:
            raise RuntimeError("Google embedding mode active but embedding call failed")
        return vec
    return hash_embed(text)


async def _detect_embed_mode() -> None:
    global _EMBED_MODE
    settings = get_settings()
    if settings.google_api_key:
        probe = await google_embed_text("mortgage policy embedding probe")
        if probe is not None:
            _EMBED_MODE = "google"
            logger.info("Policy RAG embedding mode: google (%s dims)", probe.shape[0])
            return
    _EMBED_MODE = "hash"
    logger.info("Policy RAG embedding mode: deterministic hash (%s dims)", hash_embed("probe").shape[0])


async def build_chunk_records() -> list[dict[str, Any]]:
    manifest = json.loads((data_dir() / "policy_manifest.json").read_text(encoding="utf-8"))
    records: list[dict[str, Any]] = []
    for entry in manifest:
        rel = entry["path"]
        text_path = data_dir() / "policy_documents" / rel
        raw = text_path.read_text(encoding="utf-8")
        chunks = chunk_text(raw)
        for i, chunk in enumerate(chunks):
            cid = stable_chunk_id(entry["document_id"], i, chunk)
            records.append(
                {
                    "chunk_id": cid,
                    "text": chunk,
                    "document_id": entry["document_id"],
                    "section": entry["section"],
                    "source": entry["source"],
                }
            )
    return records


async def init_policy_index() -> None:
    """Called once at process startup to warm the FAISS index for `search_mortgage_policy`."""
    global _INDEX
    if _INDEX is not None:
        return
    await _detect_embed_mode()
    chunk_records = await build_chunk_records()
    vectors = [await embed_query(c["text"]) for c in chunk_records]
    mat = np.stack(vectors, axis=0)
    _INDEX = build_ip_index(mat, chunk_records)
    logger.info("Policy FAISS index built with %s chunks", len(chunk_records))


def get_policy_index() -> PolicyIndex:
    if _INDEX is None:
        raise RuntimeError("Policy index not initialized — call init_policy_index() during app startup")
    return _INDEX


def index_version() -> str:
    return _INDEX_VERSION
