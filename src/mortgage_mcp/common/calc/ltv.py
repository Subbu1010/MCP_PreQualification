"""
MCP references: calculate_ltv, check_borrower_eligibility
Purpose: Pure LTV / CLTV math — used by the LTV MCP tool and eligibility evaluation.
"""

from __future__ import annotations


def compute_ltv_cltv(
    *,
    loan_amount: float,
    appraised_value: float,
    subordinate_financing: float = 0.0,
) -> tuple[float, float, dict[str, float]]:
    """
    Returns (ltv_percent, cltv_percent, components).

    LTV = loan / value. CLTV = (loan + subordinate) / value.
    """
    value = float(appraised_value)
    if value <= 0:
        raise ValueError("appraised_value must be greater than zero")

    loan = float(loan_amount)
    sub = float(subordinate_financing)
    if loan < 0 or sub < 0:
        raise ValueError("loan amounts cannot be negative")

    ltv = round((loan / value) * 100.0, 1)
    cltv = round(((loan + sub) / value) * 100.0, 1)
    components = {
        "loan_amount": loan,
        "appraised_value": value,
        "subordinate_financing": sub,
        "combined_liens": loan + sub,
    }
    return ltv, cltv, components
