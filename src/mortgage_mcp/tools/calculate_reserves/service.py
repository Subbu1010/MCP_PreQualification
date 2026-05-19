"""MCP references: mortgage_calculate_reserves"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from mortgage_mcp.common.errors.app_errors import VALIDATION_ERROR, ToolError
from mortgage_mcp.common.types.enums import LoanType
from mortgage_mcp.tools.calculate_reserves.schemas import CalculateReservesInput, CalculateReservesOutput

RULESET_VERSION = "uw-rules@2026.05.01"


def _guidelines() -> dict:
    path = Path(__file__).resolve().parent / "data" / "reserves_guidelines.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _load_eligibility_fixture(name: str) -> dict:
    base = Path(__file__).resolve().parents[1] / "check_borrower_eligibility" / "data" / name
    return json.loads(base.read_text(encoding="utf-8"))


async def run_calculate_reserves(raw: dict) -> dict:
    correlation_id = str(uuid.uuid4())
    try:
        payload = CalculateReservesInput.model_validate(raw)
    except Exception as exc:  # noqa: BLE001
        raise ToolError(VALIDATION_ERROR, str(exc)) from exc

    try:
        lt = LoanType(payload.loan_type.strip().upper())
    except ValueError as exc:
        raise ToolError(VALIDATION_ERROR, f"Unsupported loan_type: {payload.loan_type}") from exc

    programs = _guidelines()["programs"]
    if lt.value not in programs:
        raise ToolError(VALIDATION_ERROR, f"No reserve guideline for {lt.value}")
    required_months = float(programs[lt.value]["min_months"])

    pitia: float
    available_months: float

    if payload.borrower_id and payload.application_id:
        borrowers = _load_eligibility_fixture("borrowers.json")["borrowers"]
        apps = _load_eligibility_fixture("loan_applications.json")["applications"]
        borrower = next((b for b in borrowers if b["borrower_id"] == payload.borrower_id), None)
        app = next(
            (
                a
                for a in apps
                if a["application_id"] == payload.application_id and a["borrower_id"] == payload.borrower_id
            ),
            None,
        )
        if not borrower or not app:
            raise ToolError(VALIDATION_ERROR, "borrower_id/application_id not found in mock eligibility data")
        pitia = float(app["monthly_pitia"])
        available_months = float(borrower["reserves_months"])
    elif payload.liquid_assets_usd is not None and payload.monthly_pitia is not None:
        pitia = float(payload.monthly_pitia)
        available_months = float(payload.liquid_assets_usd) / pitia
    else:
        pitia = float(payload.monthly_pitia)  # type: ignore[arg-type]
        available_months = float(payload.reserves_months_available)  # type: ignore[arg-type]

    required_dollars = round(required_months * pitia, 2)
    available_dollars = round(available_months * pitia, 2)
    meets = available_months >= required_months

    explanation = (
        f"Mock {lt.value} guideline requires {required_months} months of PITIA (${required_dollars:,.2f}); "
        f"scenario shows {available_months:.1f} months (${available_dollars:,.2f}) — "
        f"{'meets' if meets else 'below'} guideline."
    )

    out = CalculateReservesOutput(
        correlation_id=correlation_id,
        loan_type=lt.value,
        required_months=required_months,
        available_months=round(available_months, 2),
        required_dollars=required_dollars,
        available_dollars=available_dollars,
        meets_guideline=meets,
        explanation=explanation,
        ruleset_version=RULESET_VERSION,
    )
    return out.model_dump()
