"""
MCP references: search_mortgage_policy
Purpose: Service layer for the `search_mortgage_policy` MCP tool (parameter validation + retrieval).
"""

from __future__ import annotations

import uuid
from typing import Any

from mortgage_mcp.common.errors.app_errors import VALIDATION_ERROR, ToolError
from mortgage_mcp.tools.search_mortgage_policy.bootstrap import index_version
from mortgage_mcp.tools.search_mortgage_policy.rag.retrieval import search_policy


async def run_search_mortgage_policy(raw: dict[str, Any]) -> dict[str, Any]:
    correlation_id = str(uuid.uuid4())
    query = raw.get("query")
    if not query or not isinstance(query, str):
        raise ToolError(VALIDATION_ERROR, "query is required and must be a non-empty string")

    top_k = int(raw.get("top_k", 5))
    top_k = max(1, min(top_k, 20))

    sources_raw = raw.get("sources")
    sources: set[str] | None = None
    if sources_raw:
        if isinstance(sources_raw, list):
            sources = {str(s).strip().upper() for s in sources_raw if str(s).strip()}
        elif isinstance(sources_raw, str):
            sources = {s.strip().upper() for s in sources_raw.split(",") if s.strip()}
        else:
            raise ToolError(VALIDATION_ERROR, "sources must be a list of strings or comma-separated string")

    hits = await search_policy(query=query, sources=sources, top_k=top_k)
    return {
        "success": True,
        "tool": "mortgage_search_mortgage_policy",
        "correlation_id": correlation_id,
        "index_version": index_version(),
        "hits": hits,
    }
