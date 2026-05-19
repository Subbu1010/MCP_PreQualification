"""
MCP references: explain_eligibility_decision
Purpose: Registers the `explain_eligibility_decision` MCP tool with FastMCP.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from mcp.types import ToolAnnotations

from mortgage_mcp.common.errors.app_errors import ToolError
from mortgage_mcp.common.logging.structured_logger import log_event

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

TOOL_NAME = "mortgage_explain_eligibility_decision"


def register_tools(mcp: FastMCP) -> None:
    # explain_eligibility_decision tool
    @mcp.tool(
        name=TOOL_NAME,
        title="Explain Eligibility Decision",
        description="Generate an advisory, JSON-structured explanation for a prior eligibility snapshot.",
        annotations=ToolAnnotations(title="mortgage", readOnlyHint=True),
    )
    async def explain_eligibility_decision(
        eligibility_snapshot: dict[str, Any],
        language: str = "en-US",
    ) -> dict:
        """
        Produces a narrative explanation for an eligibility snapshot via Gemini or mock provider.
        """
        from mortgage_mcp.tools.explain_eligibility_decision.service import run_explain_eligibility_decision

        payload = {"eligibility_snapshot": eligibility_snapshot, "language": language}

        try:
            result = await run_explain_eligibility_decision(payload)
            log_event(
                logger,
                event="mcp_tool_success",
                tool="explain_eligibility_decision",
                correlation_id=result.get("correlation_id"),
                model_id=result.get("model_id"),
            )
            return result
        except ToolError as exc:
            log_event(
                logger,
                event="mcp_tool_error",
                tool="explain_eligibility_decision",
                code=exc.code,
                message=exc.message,
            )
            return {"success": False, "tool": TOOL_NAME, "code": exc.code, "message": exc.message}
