"""MCP references: mortgage_compare_loan_programs"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mcp.types import ToolAnnotations

from mortgage_mcp.common.errors.app_errors import ToolError
from mortgage_mcp.common.logging.structured_logger import log_event

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

TOOL_NAME = "mortgage_compare_loan_programs"


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool(
        name=TOOL_NAME,
        title="Compare Loan Programs",
        description="Compare CONVENTIONAL, FHA, VA, and JUMBO mock thresholds for the same borrower scenario.",
        annotations=ToolAnnotations(title="mortgage", readOnlyHint=True),
    )
    async def compare_loan_programs(
        borrower_id: str,
        application_id: str,
        programs: list[str] | None = None,
    ) -> dict:
        """Returns a matrix of program eligibility and guideline limits."""
        from mortgage_mcp.tools.compare_loan_programs.service import run_compare_loan_programs

        payload: dict = {"borrower_id": borrower_id, "application_id": application_id}
        if programs is not None:
            payload["programs"] = programs

        try:
            result = await run_compare_loan_programs(payload)
            log_event(logger, event="mcp_tool_success", tool=TOOL_NAME, correlation_id=result.get("correlation_id"))
            return result
        except ToolError as exc:
            log_event(logger, event="mcp_tool_error", tool=TOOL_NAME, code=exc.code, message=exc.message)
            return {"success": False, "tool": TOOL_NAME, "code": exc.code, "message": exc.message, **exc.extra}
