"""
MCP references: calculate_dti
Purpose: Business logic for DTI calculation (optional borrower enrichment from this tool's mock data).
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from mortgage_mcp.common.calc.dti import compute_dti_ratio
from mortgage_mcp.common.errors.app_errors import VALIDATION_ERROR, ToolError
from mortgage_mcp.common.types.enums import DtiMethod
from mortgage_mcp.tools.calculate_dti.schemas import CalculateDtiInput, CalculateDtiOutput

RULESET_VERSION = "uw-rules@2026.05.01"


def _tool_data_dir() -> Path:
    return Path(__file__).resolve().parent / "data"


def _optional_borrower_adjustments(borrower_id: str | None) -> dict[str, float] | None:
    """Load optional supplemental debts from this tool's isolated mock file."""
    if not borrower_id:
        return None
    path = _tool_data_dir() / "borrower_overrides.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    for row in data.get("borrowers", []):
        if row.get("borrower_id") == borrower_id:
            return {
                "extra_monthly_debts": float(row.get("extra_monthly_debts", 0)),
            }
    raise ToolError(VALIDATION_ERROR, f"borrower_id not found in calculate_dti mock data: {borrower_id}")


async def run_calculate_dti(raw: dict) -> dict:
    correlation_id = str(uuid.uuid4())
    try:
        payload = CalculateDtiInput.model_validate(raw)
    except Exception as exc:  # noqa: BLE001 — surfaced as structured tool error
        raise ToolError(VALIDATION_ERROR, str(exc)) from exc

    extra_debts = 0.0
    if payload.borrower_id:
        adj = _optional_borrower_adjustments(payload.borrower_id)
        if adj:
            extra_debts = adj["extra_monthly_debts"]

    debts = float(payload.monthly_non_mortgage_debts) + extra_debts
    ratio, components = compute_dti_ratio(
        gross_monthly_income=payload.gross_monthly_income,
        monthly_housing_payment=payload.monthly_housing_payment,
        monthly_non_mortgage_debts=debts,
        method=payload.dti_method,
    )

    warnings: list[str] = []
    if payload.dti_method == DtiMethod.FRONT_END:
        fe = (payload.monthly_housing_payment / payload.gross_monthly_income) * 100
        if fe > 50:
            warnings.append(
                "Housing payment exceeds 50% of gross income; front-end DTI may fail conventional thresholds."
            )

    method = payload.dti_method.value
    num = float(
        components.get("total_monthly_obligations", components.get("dti_numerator_obligations", 0))
    )
    explanation = (
        f"{method.replace('_', '-').title()} DTI = obligations numerator "
        f"(${num:,.2f}) ÷ gross monthly income (${payload.gross_monthly_income:,.2f}) = {ratio}%."
    )

    out = CalculateDtiOutput(
        correlation_id=correlation_id,
        ruleset_version=RULESET_VERSION,
        dti_ratio=ratio,
        dti_method=method,
        components=components,
        explanation=explanation,
        warnings=warnings,
    )
    return out.model_dump()
