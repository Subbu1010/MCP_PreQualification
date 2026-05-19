"""MCP references: mortgage_max_affordable_loan_amount"""

from __future__ import annotations

import uuid

from mortgage_mcp.common.calc.payment import (
    max_loan_from_principal_interest,
    mock_pmi_monthly,
    monthly_principal_interest,
)
from mortgage_mcp.common.errors.app_errors import VALIDATION_ERROR, ToolError
from mortgage_mcp.tools.max_affordable_loan_amount.schemas import MaxAffordableLoanInput, MaxAffordableLoanOutput

RULESET_VERSION = "uw-rules@2026.05.01"


async def run_max_affordable_loan_amount(raw: dict) -> dict:
    correlation_id = str(uuid.uuid4())
    try:
        payload = MaxAffordableLoanInput.model_validate(raw)
    except Exception as exc:  # noqa: BLE001
        raise ToolError(VALIDATION_ERROR, str(exc)) from exc

    max_obligations = payload.gross_monthly_income * (payload.target_dti_percent / 100.0)
    max_housing = max_obligations - payload.monthly_non_mortgage_debts
    if max_housing <= 0:
        raise ToolError(
            VALIDATION_ERROR,
            "Non-mortgage debts exceed target DTI capacity; no room for housing payment.",
        )

    max_housing_after_escrow = max_housing - payload.monthly_escrow
    if max_housing_after_escrow <= 0:
        raise ToolError(VALIDATION_ERROR, "Escrow exceeds affordable housing budget at target DTI.")

    # One-pass MI estimate from provisional loan, then refine.
    provisional_loan = max_loan_from_principal_interest(
        monthly_pi=max_housing_after_escrow * 0.92,
        annual_interest_rate=payload.annual_interest_rate,
        term_years=payload.term_years,
    )
    ltv_guess = 90.0
    pmi = mock_pmi_monthly(
        loan_amount=provisional_loan,
        ltv_ratio=ltv_guess,
        loan_type=payload.loan_type.upper(),
    )
    max_pi = max_housing_after_escrow - pmi
    if max_pi <= 0:
        raise ToolError(VALIDATION_ERROR, "MI and escrow exceed affordable housing budget at target DTI.")

    max_loan = max_loan_from_principal_interest(
        monthly_pi=max_pi,
        annual_interest_rate=payload.annual_interest_rate,
        term_years=payload.term_years,
    )
    pmi = mock_pmi_monthly(
        loan_amount=max_loan,
        ltv_ratio=ltv_guess,
        loan_type=payload.loan_type.upper(),
    )
    pi = monthly_principal_interest(
        loan_amount=max_loan,
        annual_interest_rate=payload.annual_interest_rate,
        term_years=payload.term_years,
    )

    explanation = (
        f"At {payload.target_dti_percent}% back-end DTI, max housing ≈ ${max_housing:,.2f}/mo "
        f"(P&I ${pi:,.2f}, escrow ${payload.monthly_escrow:,.2f}, illustrative MI ${pmi:,.2f}) "
        f"supports ≈ ${max_loan:,.0f} loan at {payload.annual_interest_rate}% / {payload.term_years}yr."
    )

    out = MaxAffordableLoanOutput(
        correlation_id=correlation_id,
        max_total_housing_payment=round(max_housing, 2),
        max_principal_and_interest=round(pi, 2),
        max_loan_amount=round(max_loan, 2),
        assumed_monthly_pmi=pmi,
        target_dti_percent=payload.target_dti_percent,
        explanation=explanation,
        ruleset_version=RULESET_VERSION,
    )
    return out.model_dump()
