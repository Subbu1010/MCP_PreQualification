"""
MCP references: calculate_dti, check_borrower_eligibility
Purpose: Pure debt-to-income (DTI) math with no I/O — used by the DTI MCP tool and eligibility flow.
"""

from __future__ import annotations

from mortgage_mcp.common.types.enums import DtiMethod


def total_monthly_obligations(
    *,
    monthly_housing_payment: float,
    monthly_non_mortgage_debts: float,
) -> float:
    """Sum recurring monthly obligations used in back-end DTI."""
    return float(monthly_housing_payment) + float(monthly_non_mortgage_debts)


def compute_dti_ratio(
    *,
    gross_monthly_income: float,
    monthly_housing_payment: float,
    monthly_non_mortgage_debts: float,
    method: DtiMethod = DtiMethod.BACK_END,
) -> tuple[float, dict[str, float]]:
    """
    Returns (dti_percent, components).

    Front-end DTI uses housing / income only; back-end uses total obligations / income.
    """
    if gross_monthly_income <= 0:
        raise ValueError("gross_monthly_income must be greater than zero")

    housing = float(monthly_housing_payment)
    debts = float(monthly_non_mortgage_debts)
    income = float(gross_monthly_income)

    if method == DtiMethod.FRONT_END:
        numerator = housing
        components = {
            "gross_monthly_income": income,
            "monthly_housing_payment": housing,
            "monthly_non_mortgage_debts": debts,
            "dti_numerator_obligations": numerator,
        }
    else:
        numerator = total_monthly_obligations(
            monthly_housing_payment=housing,
            monthly_non_mortgage_debts=debts,
        )
        components = {
            "gross_monthly_income": income,
            "monthly_housing_payment": housing,
            "monthly_non_mortgage_debts": debts,
            "total_monthly_obligations": numerator,
        }

    ratio = round((numerator / income) * 100.0, 1)
    return ratio, components
