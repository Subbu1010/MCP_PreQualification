"""MCP references: mortgage_max_affordable_loan_amount"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mcp.types import ToolAnnotations

from mortgage_mcp.common.errors.app_errors import ToolError
from mortgage_mcp.common.logging.structured_logger import log_event

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

TOOL_NAME = "mortgage_max_affordable_loan_amount"


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool(
        name=TOOL_NAME,
        title="Max Affordable Loan Amount",
        description="Reverse-solve maximum loan amount from income, debts, target DTI, rate, and escrow.",
        annotations=ToolAnnotations(title="mortgage", readOnlyHint=True),
    )
    async def max_affordable_loan_amount(
        gross_monthly_income: float,
        monthly_non_mortgage_debts: float = 0.0,
        target_dti_percent: float = 45.0,
        annual_interest_rate: float = 6.5,
        term_years: int = 30,
        monthly_escrow: float = 0.0,
        loan_type: str = "CONVENTIONAL",
    ) -> dict:
        """Returns max loan and housing payment at the target back-end DTI."""
        from mortgage_mcp.tools.max_affordable_loan_amount.service import run_max_affordable_loan_amount

        payload = {
            "gross_monthly_income": gross_monthly_income,
            "monthly_non_mortgage_debts": monthly_non_mortgage_debts,
            "target_dti_percent": target_dti_percent,
            "annual_interest_rate": annual_interest_rate,
            "term_years": term_years,
            "monthly_escrow": monthly_escrow,
            "loan_type": loan_type,
        }

        try:
            result = await run_max_affordable_loan_amount(payload)
            log_event(logger, event="mcp_tool_success", tool=TOOL_NAME, correlation_id=result.get("correlation_id"))
            return result
        except ToolError as exc:
            log_event(logger, event="mcp_tool_error", tool=TOOL_NAME, code=exc.code, message=exc.message)
            return {"success": False, "tool": TOOL_NAME, "code": exc.code, "message": exc.message, **exc.extra}
