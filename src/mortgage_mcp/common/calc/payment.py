"""
MCP references: estimate_monthly_payment, max_affordable_loan_amount
Purpose: Amortization and inverse principal helpers (pure functions, no I/O).
"""

from __future__ import annotations


def monthly_principal_interest(
    *,
    loan_amount: float,
    annual_interest_rate: float,
    term_years: int,
) -> float:
    """Fixed-rate fully amortizing monthly P&I."""
    if loan_amount <= 0:
        return 0.0
    n = term_years * 12
    if n <= 0:
        raise ValueError("term_years must be positive")
    if annual_interest_rate <= 0:
        return loan_amount / n
    r = annual_interest_rate / 100.0 / 12.0
    factor = (1.0 + r) ** n
    return loan_amount * r * factor / (factor - 1.0)


def max_loan_from_principal_interest(
    *,
    monthly_pi: float,
    annual_interest_rate: float,
    term_years: int,
) -> float:
    """Inverse of monthly_principal_interest for affordability caps."""
    if monthly_pi <= 0:
        return 0.0
    n = term_years * 12
    if n <= 0:
        raise ValueError("term_years must be positive")
    if annual_interest_rate <= 0:
        return monthly_pi * n
    r = annual_interest_rate / 100.0 / 12.0
    factor = (1.0 + r) ** n
    return monthly_pi * (factor - 1.0) / (r * factor)


def mock_pmi_monthly(*, loan_amount: float, ltv_ratio: float, loan_type: str) -> float:
    """Illustrative monthly MI — not a rate quote."""
    if loan_type in {"VA", "VA_LOAN"}:
        return 0.0
    if loan_type == "FHA":
        return round(loan_amount * 0.0055 / 12.0, 2)
    if ltv_ratio <= 80.0:
        return 0.0
    factor = 0.0075 if ltv_ratio <= 90.0 else 0.0095
    return round(loan_amount * factor / 12.0, 2)
