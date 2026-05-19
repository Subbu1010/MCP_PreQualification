"""
MCP references: check_borrower_eligibility
Purpose: Registers the `check_borrower_eligibility` MCP tool with FastMCP.
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

TOOL_NAME = "mortgage_check_borrower_eligibility"


def register_tools(mcp: FastMCP) -> None:
    # check_borrower_eligibility tool
    @mcp.tool(
        name=TOOL_NAME,
        title="Check Borrower Eligibility",
        description="Run mock underwriting pre-check: credit, DTI, LTV, reserves, with explainable outputs.",
        annotations=ToolAnnotations(title="mortgage", readOnlyHint=True),
    )
    async def check_borrower_eligibility(
        borrower_id: str,
        application_id: str,
        loan_type: str,
    ) -> dict:
        """
        Evaluates borrower and application against mock enterprise prequalification rules.
        """
        from mortgage_mcp.tools.check_borrower_eligibility.service import run_check_borrower_eligibility

        payload = {
            "borrower_id": borrower_id,
            "application_id": application_id,
            "loan_type": loan_type,
        }

        try:
            result = await run_check_borrower_eligibility(payload)
            log_event(
                logger,
                event="mcp_tool_success",
                tool="check_borrower_eligibility",
                correlation_id=result.get("correlation_id"),
                eligible=result.get("eligible"),
            )
            return result
        except ToolError as exc:
            log_event(
                logger,
                event="mcp_tool_error",
                tool="check_borrower_eligibility",
                code=exc.code,
                message=exc.message,
            )
            return {
                "success": False,
                "tool": TOOL_NAME,
                "code": exc.code,
                "message": exc.message,
                **exc.extra,
            }
