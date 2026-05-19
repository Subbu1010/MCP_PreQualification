"""Unit tests for shared payment amortization helpers."""

from __future__ import annotations

from mortgage_mcp.common.calc.payment import (
    max_loan_from_principal_interest,
    monthly_principal_interest,
)


def test_monthly_pi_roundtrip() -> None:
    loan = 450_000.0
    rate = 6.5
    term = 30
    pi = monthly_principal_interest(loan_amount=loan, annual_interest_rate=rate, term_years=term)
    back = max_loan_from_principal_interest(monthly_pi=pi, annual_interest_rate=rate, term_years=term)
    assert abs(back - loan) < 1.0
