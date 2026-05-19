"""MCP references: mortgage_calculate_reserves"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mcp.types import ToolAnnotations

from mortgage_mcp.common.errors.app_errors import ToolError
from mortgage_mcp.common.logging.structured_logger import log_event

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

TOOL_NAME = "mortgage_calculate_reserves"


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool(
        name=TOOL_NAME,
        title="Calculate Reserves",
        description="Compare post-close liquid reserves (months and dollars) to mock program guidelines.",
        annotations=ToolAnnotations(title="mortgage", readOnlyHint=True),
    )
    async def calculate_reserves(
        loan_type: str,
        borrower_id: str | None = None,
        application_id: str | None = None,
        liquid_assets_usd: float | None = None,
        monthly_pitia: float | None = None,
        reserves_months_available: float | None = None,
    ) -> dict:
        """Evaluates reserve months vs mock CONVENTIONAL/FHA/VA/JUMBO requirements."""
        from mortgage_mcp.tools.calculate_reserves.service import run_calculate_reserves

        payload: dict = {"loan_type": loan_type}
        if borrower_id is not None:
            payload["borrower_id"] = borrower_id
        if application_id is not None:
            payload["application_id"] = application_id
        if liquid_assets_usd is not None:
            payload["liquid_assets_usd"] = liquid_assets_usd
        if monthly_pitia is not None:
            payload["monthly_pitia"] = monthly_pitia
        if reserves_months_available is not None:
            payload["reserves_months_available"] = reserves_months_available

        try:
            result = await run_calculate_reserves(payload)
            log_event(logger, event="mcp_tool_success", tool=TOOL_NAME, correlation_id=result.get("correlation_id"))
            return result
        except ToolError as exc:
            log_event(logger, event="mcp_tool_error", tool=TOOL_NAME, code=exc.code, message=exc.message)
            return {"success": False, "tool": TOOL_NAME, "code": exc.code, "message": exc.message, **exc.extra}
