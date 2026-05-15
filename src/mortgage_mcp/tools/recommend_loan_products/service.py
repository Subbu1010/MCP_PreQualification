"""
MCP references: recommend_loan_products
Purpose: Ranks mock catalog products using duplicated borrower/application JSON in this tool folder.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from mortgage_mcp.common.calc.dti import compute_dti_ratio
from mortgage_mcp.common.calc.ltv import compute_ltv_cltv
from mortgage_mcp.common.errors.app_errors import BUSINESS_RULE_VIOLATION, VALIDATION_ERROR, ToolError
from mortgage_mcp.common.types.enums import DtiMethod, LoanType
from mortgage_mcp.tools.recommend_loan_products.schemas import RecommendLoanProductsInput

RULESET_VERSION = "uw-rules@2026.05.01"


def _data_dir() -> Path:
    return Path(__file__).resolve().parent / "data"


def _load_json(name: str) -> dict:
    return json.loads((_data_dir() / name).read_text(encoding="utf-8"))


def _borrower(borrower_id: str) -> dict:
    for b in _load_json("borrowers.json")["borrowers"]:
        if b["borrower_id"] == borrower_id:
            return b
    raise ToolError(VALIDATION_ERROR, f"borrower_id not found in recommend_loan_products mock data: {borrower_id}")


def _application(application_id: str, borrower_id: str) -> dict:
    for a in _load_json("loan_applications.json")["applications"]:
        if a["application_id"] == application_id and a["borrower_id"] == borrower_id:
            return a
    raise ToolError(VALIDATION_ERROR, f"application not found for borrower in recommend_loan_products mock data")


async def run_recommend_loan_products(raw: dict) -> dict:
    correlation_id = str(uuid.uuid4())
    try:
        payload = RecommendLoanProductsInput.model_validate(raw)
    except Exception as exc:  # noqa: BLE001
        raise ToolError(VALIDATION_ERROR, str(exc)) from exc

    borrower = _borrower(payload.borrower_id)
    application = _application(payload.application_id, payload.borrower_id)

    lt = LoanType(str(application["loan_type"]).upper())
    gross_monthly_income = float(borrower["annual_income"]) / 12.0
    dti, _ = compute_dti_ratio(
        gross_monthly_income=gross_monthly_income,
        monthly_housing_payment=float(application["monthly_pitia"]),
        monthly_non_mortgage_debts=float(borrower["monthly_non_housing_debts"]),
        method=DtiMethod.BACK_END,
    )
    ltv, _, _ = compute_ltv_cltv(
        loan_amount=float(application["loan_amount"]),
        appraised_value=float(application["appraised_value"]),
        subordinate_financing=float(application.get("subordinate_financing", 0)),
    )

    fico = int(borrower["credit_score"])
    candidates: list[dict] = []
    for p in _load_json("mortgage_products.json")["products"]:
        if p["program"] != lt.value:
            continue
        if fico < int(p["min_fico"]):
            continue
        if ltv > float(p["max_ltv"]):
            continue
        if payload.fixed_only and "ARM" in p["tags"]:
            continue
        if payload.eligible_only:
            # lightweight mock gate: DTI <= 45 for conventional-style programs
            if lt == LoanType.CONVENTIONAL and dti > 45.0:
                continue
            if lt == LoanType.JUMBO and dti > 43.0:
                continue
        candidates.append(p)

    if not candidates:
        raise ToolError(
            BUSINESS_RULE_VIOLATION,
            "No products match filters and eligibility constraints",
            extra={"correlation_id": correlation_id},
        )

    def score(prod: dict) -> float:
        s = 0.7
        if "FIXED" in prod["tags"]:
            s += 0.15
        if prod["estimated_note_rate"] <= 6.4:
            s += 0.1
        s += (min(fico, 850) - 600) / 800 * 0.05
        return round(min(s, 0.99), 2)

    ranked = sorted(candidates, key=score, reverse=True)
    recommendations = []
    for prod in ranked[:5]:
        recommendations.append(
            {
                "product_code": prod["product_code"],
                "score": score(prod),
                "rationale": (
                    f"Matches program {lt.value}; within min FICO {prod['min_fico']} and max LTV {prod['max_ltv']}%; "
                    f"mock estimated note rate {prod['estimated_note_rate']}%."
                ),
                "estimated_note_rate_apr_stub": {
                    "note_rate": prod["estimated_note_rate"],
                    "apr": round(float(prod["estimated_note_rate"]) + 0.12, 3),
                    "disclaimer": "Illustrative mock pricing; not a Loan Estimate.",
                },
            }
        )

    return {
        "success": True,
        "tool": "recommend_loan_products",
        "correlation_id": correlation_id,
        "recommendations": recommendations,
        "ruleset_version": RULESET_VERSION,
        "inputs_echo": {"dti_ratio": dti, "ltv_ratio": ltv, "loan_type": lt.value},
    }
