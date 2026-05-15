"""
MCP references: calculate_dti, check_borrower_eligibility
Purpose: Unit tests for shared DTI math and eligibility orchestration (pytest).
"""

from __future__ import annotations

import pytest

from mortgage_mcp.common.calc.dti import compute_dti_ratio
from mortgage_mcp.common.types.enums import DtiMethod
from mortgage_mcp.tools.check_borrower_eligibility.service import run_check_borrower_eligibility


def test_compute_dti_back_end() -> None:
    ratio, parts = compute_dti_ratio(
        gross_monthly_income=10_000,
        monthly_housing_payment=3_000,
        monthly_non_mortgage_debts=500,
        method=DtiMethod.BACK_END,
    )
    assert ratio == 35.0
    assert parts["total_monthly_obligations"] == 3500


@pytest.mark.asyncio
async def test_eligibility_approved_path() -> None:
    out = await run_check_borrower_eligibility(
        {"borrower_id": "BRW-10001", "application_id": "APP-50021", "loan_type": "CONVENTIONAL"}
    )
    assert out["success"] is True
    assert out["eligible"] is True
    assert out["status"] == "APPROVED"


@pytest.mark.asyncio
async def test_eligibility_declined_path() -> None:
    out = await run_check_borrower_eligibility(
        {"borrower_id": "BRW-10002", "application_id": "APP-50022", "loan_type": "CONVENTIONAL"}
    )
    assert out["eligible"] is False
    assert out["status"] == "DECLINED"
