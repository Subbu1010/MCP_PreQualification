"""Tests for newly added MCP tool service layers."""

from __future__ import annotations

import pytest

from mortgage_mcp.tools.calculate_reserves.service import run_calculate_reserves
from mortgage_mcp.tools.compare_loan_programs.service import run_compare_loan_programs
from mortgage_mcp.tools.estimate_monthly_payment.service import run_estimate_monthly_payment
from mortgage_mcp.tools.generate_prequal_summary.service import run_generate_prequal_summary
from mortgage_mcp.tools.max_affordable_loan_amount.service import run_max_affordable_loan_amount


@pytest.mark.asyncio
async def test_estimate_monthly_payment() -> None:
    out = await run_estimate_monthly_payment(
        {
            "loan_amount": 450000,
            "annual_interest_rate": 6.5,
            "term_years": 30,
            "appraised_value": 550000,
        }
    )
    assert out["success"] is True
    assert out["total_monthly_payment"] > 0


@pytest.mark.asyncio
async def test_calculate_reserves_alex() -> None:
    out = await run_calculate_reserves(
        {
            "borrower_id": "BRW-10001",
            "application_id": "APP-50021",
            "loan_type": "CONVENTIONAL",
        }
    )
    assert out["meets_guideline"] is True


@pytest.mark.asyncio
async def test_max_affordable_loan() -> None:
    out = await run_max_affordable_loan_amount(
        {
            "gross_monthly_income": 10416.67,
            "monthly_non_mortgage_debts": 950,
            "target_dti_percent": 45.0,
            "annual_interest_rate": 6.5,
        }
    )
    assert out["max_loan_amount"] > 100_000


@pytest.mark.asyncio
async def test_compare_programs() -> None:
    out = await run_compare_loan_programs(
        {"borrower_id": "BRW-10001", "application_id": "APP-50021"}
    )
    assert len(out["comparisons"]) == 4


@pytest.mark.asyncio
async def test_prequal_summary() -> None:
    out = await run_generate_prequal_summary(
        {
            "borrower_id": "BRW-10001",
            "application_id": "APP-50021",
            "loan_type": "CONVENTIONAL",
        }
    )
    assert out["summary"]["status"] == "APPROVED"
