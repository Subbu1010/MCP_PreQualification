"""
MCP references: search_mortgage_policy
Purpose: Performs semantic-ish retrieval over the FAISS index built from this tool's policy corpus.
"""

from __future__ import annotations

from typing import Any

from mortgage_mcp.tools.search_mortgage_policy.bootstrap import embed_query, get_policy_index
from mortgage_mcp.tools.search_mortgage_policy.rag.citations import build_hit


async def search_policy(
    *,
    query: str,
    sources: set[str] | None,
    top_k: int,
) -> list[dict[str, Any]]:
    index = get_policy_index()
    q = await embed_query(query)
    hits = index.search(q, top_k=max(top_k * 4, top_k + 5))
    results: list[dict[str, Any]] = []
    for score, chunk in hits:
        src = chunk["source"]
        if sources and src not in sources:
            continue
        results.append(
            build_hit(
                chunk_id=chunk["chunk_id"],
                score=score,
                document_id=chunk["document_id"],
                section=chunk["section"],
                snippet=chunk["text"][:800],
                source=src,
            )
        )
    return results[:top_k]
