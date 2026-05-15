"""
MCP references: calculate_ltv
Purpose: Registers the `calculate_ltv` MCP tool with FastMCP.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mortgage_mcp.common.errors.app_errors import ToolError
from mortgage_mcp.common.logging.structured_logger import log_event

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


async def calculate_ltv(
    loan_amount: float,
    appraised_value: float,
    subordinate_financing: float = 0.0,
    ltv_basis: str = "PURCHASE",
) -> dict:
    """MCP tool: calculate_ltv — loan-to-value and combined LTV for mock underwriting."""
    from mortgage_mcp.tools.calculate_ltv.service import run_calculate_ltv

    payload = {
        "loan_amount": loan_amount,
        "appraised_value": appraised_value,
        "subordinate_financing": subordinate_financing,
        "ltv_basis": ltv_basis,
    }

    try:
        result = await run_calculate_ltv(payload)
        log_event(
            logger,
            event="mcp_tool_success",
            tool="calculate_ltv",
            correlation_id=result.get("correlation_id"),
        )
        return result
    except ToolError as exc:
        log_event(logger, event="mcp_tool_error", tool="calculate_ltv", code=exc.code, message=exc.message)
        return {"success": False, "tool": "calculate_ltv", "code": exc.code, "message": exc.message, **exc.extra}


def register_tools(mcp: FastMCP) -> None:
    mcp.add_tool(
        calculate_ltv,
        name="calculate_ltv",
        description="Calculate LTV and CLTV from loan amount, appraised value, and subordinate financing.",
    )
