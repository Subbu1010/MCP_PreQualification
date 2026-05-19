"""MCP references: mortgage_estimate_monthly_payment"""

from __future__ import annotations

import uuid

from mortgage_mcp.common.calc.ltv import compute_ltv_cltv
from mortgage_mcp.common.calc.payment import mock_pmi_monthly, monthly_principal_interest
from mortgage_mcp.common.errors.app_errors import VALIDATION_ERROR, ToolError
from mortgage_mcp.tools.estimate_monthly_payment.schemas import (
    EstimateMonthlyPaymentInput,
    EstimateMonthlyPaymentOutput,
)

RULESET_VERSION = "uw-rules@2026.05.01"


async def run_estimate_monthly_payment(raw: dict) -> dict:
    correlation_id = str(uuid.uuid4())
    try:
        payload = EstimateMonthlyPaymentInput.model_validate(raw)
    except Exception as exc:  # noqa: BLE001
        raise ToolError(VALIDATION_ERROR, str(exc)) from exc

    pi = monthly_principal_interest(
        loan_amount=payload.loan_amount,
        annual_interest_rate=payload.annual_interest_rate,
        term_years=payload.term_years,
    )
    ltv: float | None = None
    if payload.appraised_value:
        ltv, _, _ = compute_ltv_cltv(
            loan_amount=payload.loan_amount,
            appraised_value=payload.appraised_value,
            subordinate_financing=0,
        )
    pmi = mock_pmi_monthly(
        loan_amount=payload.loan_amount,
        ltv_ratio=ltv or 85.0,
        loan_type=payload.loan_type.upper(),
    )
    escrow = payload.monthly_property_tax + payload.monthly_insurance + payload.monthly_hoa
    total = round(pi + pmi + escrow, 2)

    explanation = (
        f"P&I ${pi:,.2f} at {payload.annual_interest_rate}% over {payload.term_years} years on "
        f"${payload.loan_amount:,.0f}; escrow ${escrow:,.2f}; illustrative MI ${pmi:,.2f}."
    )

    out = EstimateMonthlyPaymentOutput(
        correlation_id=correlation_id,
        principal_and_interest=round(pi, 2),
        monthly_pmi=pmi,
        monthly_escrow=round(escrow, 2),
        total_monthly_payment=total,
        ltv_ratio=ltv,
        explanation=explanation,
        ruleset_version=RULESET_VERSION,
    )
    return out.model_dump()
