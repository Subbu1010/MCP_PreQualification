"""
MCP references: search_mortgage_policy
Purpose: Registers the `search_mortgage_policy` MCP tool with FastMCP.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mcp.types import ToolAnnotations

from mortgage_mcp.common.errors.app_errors import ToolError
from mortgage_mcp.common.logging.structured_logger import log_event

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

TOOL_NAME = "mortgage_search_mortgage_policy"


def register_tools(mcp: FastMCP) -> None:
    # search_mortgage_policy tool
    @mcp.tool(
        name=TOOL_NAME,
        title="Search Mortgage Policy",
        description="Search mock FHA/FNMA/Freddie/CFPB/internal policy excerpts via FAISS + embeddings.",
        annotations=ToolAnnotations(title="mortgage", readOnlyHint=True),
    )
    async def search_mortgage_policy(
        query: str,
        top_k: int = 5,
        sources: list[str] | None = None,
    ) -> dict:
        """
        Retrieves policy passages for a natural-language query from the local mock corpus.
        """
        from mortgage_mcp.tools.search_mortgage_policy.service import run_search_mortgage_policy

        payload: dict = {"query": query, "top_k": top_k}
        if sources is not None:
            payload["sources"] = sources

        try:
            result = await run_search_mortgage_policy(payload)
            log_event(
                logger,
                event="mcp_tool_success",
                tool="search_mortgage_policy",
                correlation_id=result.get("correlation_id"),
                hits=len(result.get("hits", [])),
            )
            return result
        except ToolError as exc:
            log_event(
                logger,
                event="mcp_tool_error",
                tool="search_mortgage_policy",
                code=exc.code,
                message=exc.message,
            )
            return {"success": False, "tool": TOOL_NAME, "code": exc.code, "message": exc.message}
