"""
MCP references: calculate_ltv
Purpose: Computes LTV/CLTV and PMI hint text based on static conventional heuristic (mock advisory).
"""

from __future__ import annotations

import uuid

from mortgage_mcp.common.calc.ltv import compute_ltv_cltv
from mortgage_mcp.common.errors.app_errors import VALIDATION_ERROR, ToolError
from mortgage_mcp.tools.calculate_ltv.schemas import CalculateLtvInput, CalculateLtvOutput

RULESET_VERSION = "uw-rules@2026.05.01"


async def run_calculate_ltv(raw: dict) -> dict:
    correlation_id = str(uuid.uuid4())
    try:
        payload = CalculateLtvInput.model_validate(raw)
    except Exception as exc:  # noqa: BLE001
        raise ToolError(VALIDATION_ERROR, str(exc)) from exc

    try:
        ltv, cltv, components = compute_ltv_cltv(
            loan_amount=payload.loan_amount,
            appraised_value=payload.appraised_value,
            subordinate_financing=payload.subordinate_financing,
        )
    except ValueError as exc:
        raise ToolError(VALIDATION_ERROR, str(exc)) from exc

    pmi_hint = None
    if ltv > 80.0:
        pmi_hint = (
            "Likely PMI required for conventional financing above 80% LTV per active mock ruleset; "
            "final determination subject to mortgage insurance guidelines."
        )

    explanation = (
        f"LTV = loan amount (${components['loan_amount']:,.0f}) ÷ appraised value "
        f"(${components['appraised_value']:,.0f}) = {ltv}%."
    )
    if payload.subordinate_financing > 0:
        explanation += (
            f" CLTV includes subordinate financing (${components['subordinate_financing']:,.0f}) "
            f"for a CLTV of {cltv}%."
        )

    out = CalculateLtvOutput(
        correlation_id=correlation_id,
        ltv_ratio=ltv,
        cltv_ratio=cltv,
        explanation=explanation,
        pmi_required_hint=pmi_hint,
        ruleset_version=RULESET_VERSION,
    )
    return out.model_dump()
