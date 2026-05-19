"""MCP references: mortgage_generate_prequal_summary"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mcp.types import ToolAnnotations

from mortgage_mcp.common.errors.app_errors import ToolError
from mortgage_mcp.common.logging.structured_logger import log_event

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

TOOL_NAME = "mortgage_generate_prequal_summary"


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool(
        name=TOOL_NAME,
        title="Generate Prequal Summary",
        description="Orchestrates eligibility, reserves, and product recommendations into one prequal packet.",
        annotations=ToolAnnotations(title="mortgage", readOnlyHint=True),
    )
    async def generate_prequal_summary(
        borrower_id: str,
        application_id: str,
        loan_type: str = "CONVENTIONAL",
        include_product_recommendations: bool = True,
    ) -> dict:
        """Returns a consolidated JSON summary for agents and downstream MCP clients."""
        from mortgage_mcp.tools.generate_prequal_summary.service import run_generate_prequal_summary

        payload = {
            "borrower_id": borrower_id,
            "application_id": application_id,
            "loan_type": loan_type,
            "include_product_recommendations": include_product_recommendations,
        }

        try:
            result = await run_generate_prequal_summary(payload)
            log_event(logger, event="mcp_tool_success", tool=TOOL_NAME, correlation_id=result.get("correlation_id"))
            return result
        except ToolError as exc:
            log_event(logger, event="mcp_tool_error", tool=TOOL_NAME, code=exc.code, message=exc.message)
            return {"success": False, "tool": TOOL_NAME, "code": exc.code, "message": exc.message, **exc.extra}
