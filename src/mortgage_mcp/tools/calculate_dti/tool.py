"""
MCP references: calculate_dti
Purpose: Registers the `calculate_dti` MCP tool with FastMCP (Streamable HTTP).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mortgage_mcp.common.errors.app_errors import ToolError
from mortgage_mcp.common.logging.structured_logger import log_event

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


async def calculate_dti(
    gross_monthly_income: float,
    monthly_housing_payment: float,
    monthly_non_mortgage_debts: float,
    dti_method: str = "BACK_END",
    borrower_id: str | None = None,
) -> dict:
    """
    MCP tool: calculate_dti

    Computes debt-to-income using gross monthly income and monthly obligations.
    (Explicit parameters so MCP clients send a flat JSON object, not a nested `kwargs` wrapper.)
    """
    from mortgage_mcp.tools.calculate_dti.service import run_calculate_dti

    payload: dict = {
        "gross_monthly_income": gross_monthly_income,
        "monthly_housing_payment": monthly_housing_payment,
        "monthly_non_mortgage_debts": monthly_non_mortgage_debts,
        "dti_method": dti_method,
    }
    if borrower_id is not None:
        payload["borrower_id"] = borrower_id

    try:
        result = await run_calculate_dti(payload)
        log_event(
            logger,
            event="mcp_tool_success",
            tool="calculate_dti",
            correlation_id=result.get("correlation_id"),
        )
        return result
    except ToolError as exc:
        log_event(
            logger,
            event="mcp_tool_error",
            tool="calculate_dti",
            code=exc.code,
            message=exc.message,
        )
        return {
            "success": False,
            "tool": "calculate_dti",
            "code": exc.code,
            "message": exc.message,
            **exc.extra,
        }


def register_tools(mcp: FastMCP) -> None:
    mcp.add_tool(
        calculate_dti,
        name="calculate_dti",
        description="Calculate DTI (front-end or back-end) from income and monthly obligations.",
    )
