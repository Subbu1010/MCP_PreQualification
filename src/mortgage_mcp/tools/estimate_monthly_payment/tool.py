"""MCP references: mortgage_estimate_monthly_payment"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mcp.types import ToolAnnotations

from mortgage_mcp.common.errors.app_errors import ToolError
from mortgage_mcp.common.logging.structured_logger import log_event

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

TOOL_NAME = "mortgage_estimate_monthly_payment"


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool(
        name=TOOL_NAME,
        title="Estimate Monthly Payment",
        description="Estimate P&I, escrow, and illustrative PMI/MIP for a mock monthly housing payment (PITIA).",
        annotations=ToolAnnotations(title="mortgage", readOnlyHint=True),
    )
    async def estimate_monthly_payment(
        loan_amount: float,
        annual_interest_rate: float,
        term_years: int = 30,
        monthly_property_tax: float = 0.0,
        monthly_insurance: float = 0.0,
        monthly_hoa: float = 0.0,
        loan_type: str = "CONVENTIONAL",
        appraised_value: float | None = None,
    ) -> dict:
        """Returns principal & interest, escrow, MI, and total monthly payment."""
        from mortgage_mcp.tools.estimate_monthly_payment.service import run_estimate_monthly_payment

        payload = {
            "loan_amount": loan_amount,
            "annual_interest_rate": annual_interest_rate,
            "term_years": term_years,
            "monthly_property_tax": monthly_property_tax,
            "monthly_insurance": monthly_insurance,
            "monthly_hoa": monthly_hoa,
            "loan_type": loan_type,
        }
        if appraised_value is not None:
            payload["appraised_value"] = appraised_value

        try:
            result = await run_estimate_monthly_payment(payload)
            log_event(logger, event="mcp_tool_success", tool=TOOL_NAME, correlation_id=result.get("correlation_id"))
            return result
        except ToolError as exc:
            log_event(logger, event="mcp_tool_error", tool=TOOL_NAME, code=exc.code, message=exc.message)
            return {"success": False, "tool": TOOL_NAME, "code": exc.code, "message": exc.message, **exc.extra}
