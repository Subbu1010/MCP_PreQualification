"""
MCP references: calculate_dti, calculate_ltv, check_borrower_eligibility, recommend_loan_products,
                 search_mortgage_policy, explain_eligibility_decision
Purpose: Composes the shared FastMCP server instance and registers every MCP tool from `tools/*/tool.py`.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mortgage_mcp.tools.calculate_dti.tool import register_tools as register_calculate_dti
from mortgage_mcp.tools.calculate_ltv.tool import register_tools as register_calculate_ltv
from mortgage_mcp.tools.calculate_reserves.tool import register_tools as register_calculate_reserves
from mortgage_mcp.tools.check_borrower_eligibility.tool import register_tools as register_check_eligibility
from mortgage_mcp.tools.compare_loan_programs.tool import register_tools as register_compare_programs
from mortgage_mcp.tools.estimate_monthly_payment.tool import register_tools as register_estimate_payment
from mortgage_mcp.tools.explain_eligibility_decision.tool import register_tools as register_explain
from mortgage_mcp.tools.generate_prequal_summary.tool import register_tools as register_prequal_summary
from mortgage_mcp.tools.max_affordable_loan_amount.tool import register_tools as register_max_affordable
from mortgage_mcp.tools.recommend_loan_products.tool import register_tools as register_recommend
from mortgage_mcp.tools.search_mortgage_policy.tool import register_tools as register_search_policy


def build_mortgage_mcp() -> FastMCP:
    """
    Creates the FastMCP application for Streamable HTTP.

    Each `register_*` import is isolated: removing a tool package removes its registration line here.
    """
    mcp = FastMCP(
        "Mortgage Eligibility & Prequalification MCP",
        stateless_http=True,
        json_response=True,
    )
    # When mounting at `/mcp` on the outer FastAPI app, serve MCP at `/` of the mounted sub-app.
    mcp.settings.streamable_http_path = "/"

    register_calculate_dti(mcp)
    register_calculate_ltv(mcp)
    register_estimate_payment(mcp)
    register_calculate_reserves(mcp)
    register_max_affordable(mcp)
    register_check_eligibility(mcp)
    register_compare_programs(mcp)
    register_recommend(mcp)
    register_prequal_summary(mcp)
    register_search_policy(mcp)
    register_explain(mcp)

    return mcp
