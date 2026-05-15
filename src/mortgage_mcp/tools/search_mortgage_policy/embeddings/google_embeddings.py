"""
MCP references: search_mortgage_policy
Purpose: Optional Google Generative Language embedding client (HTTP) used only by policy search RAG.
"""

from __future__ import annotations

import logging
from typing import Final

import httpx
import numpy as np

from mortgage_mcp.common.settings import get_settings

logger = logging.getLogger(__name__)

_URL_TEMPLATE: Final[str] = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent"
)


async def google_embed_text(text: str) -> np.ndarray | None:
    """
    Returns a normalized float32 embedding vector, or None if not configured / on failure.

    Note: Your organization may later swap this for Vertex AI SDK calls without touching RAG code.
    """
    settings = get_settings()
    if not settings.google_api_key:
        return None

    url = _URL_TEMPLATE.format(model=settings.google_embedding_model)
    params = {"key": settings.google_api_key}
    payload = {"content": {"parts": [{"text": text}]}}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, params=params, json=payload)
            resp.raise_for_status()
            data = resp.json()
            values = data["embedding"]["values"]
            vec = np.array(values, dtype=np.float32)
            vec = vec / (np.linalg.norm(vec) + 1e-8)
            return vec
    except Exception as exc:  # noqa: BLE001
        logger.warning("Google embedding failed; falling back to hash embeddings: %s", exc)
        return None
