"""
MCP references: search_mortgage_policy
Purpose: Normalizes citation metadata returned to MCP clients for policy hits.
"""

from __future__ import annotations

from typing import Any


def build_hit(
    *,
    chunk_id: str,
    score: float,
    document_id: str,
    section: str,
    snippet: str,
    source: str,
    effective_date: str = "2026-01-01",
) -> dict[str, Any]:
    return {
        "chunk_id": chunk_id,
        "score": round(float(score), 4),
        "document_id": document_id,
        "section": section,
        "snippet": snippet,
        "citation": {
            "label": f"{source} — {section}",
            "effective_date": effective_date,
        },
    }
