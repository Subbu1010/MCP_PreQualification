"""
MCP references: recommend_loan_products
Purpose: Registers the `recommend_loan_products` MCP tool with FastMCP.
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

TOOL_NAME = "mortgage_recommend_loan_products"


def register_tools(mcp: FastMCP) -> None:
    # recommend_loan_products tool
    @mcp.tool(
        name=TOOL_NAME,
        title="Recommend Loan Products",
        description="Recommend ranked loan products from this tool's isolated mock product catalog.",
        annotations=ToolAnnotations(title="mortgage", readOnlyHint=True),
    )
    async def recommend_loan_products(
        borrower_id: str,
        application_id: str,
        fixed_only: bool = False,
        max_discount_points: float = 99.0,
        eligible_only: bool = True,
    ) -> dict:
        """
        Ranks mock mortgage products for a borrower and application pair.
        """
        from mortgage_mcp.tools.recommend_loan_products.service import run_recommend_loan_products

        payload = {
            "borrower_id": borrower_id,
            "application_id": application_id,
            "fixed_only": fixed_only,
            "max_discount_points": max_discount_points,
            "eligible_only": eligible_only,
        }

        try:
            result = await run_recommend_loan_products(payload)
            log_event(
                logger,
                event="mcp_tool_success",
                tool="recommend_loan_products",
                correlation_id=result.get("correlation_id"),
            )
            return result
        except ToolError as exc:
            log_event(
                logger,
                event="mcp_tool_error",
                tool="recommend_loan_products",
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
