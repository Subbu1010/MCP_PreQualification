"""
MCP references: calculate_dti, calculate_ltv, check_borrower_eligibility
Purpose: Exposes pure DTI/LTV calculators for MCP tools and eligibility orchestration.
"""

from mortgage_mcp.common.calc.dti import compute_dti_ratio, total_monthly_obligations
from mortgage_mcp.common.calc.ltv import compute_ltv_cltv

__all__ = ["compute_dti_ratio", "total_monthly_obligations", "compute_ltv_cltv"]
