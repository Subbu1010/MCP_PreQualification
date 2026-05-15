"""
MCP references: check_borrower_eligibility
Purpose: Orchestrates mock data + DTI/LTV calculations + rules engine for prequalification outcomes.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from mortgage_mcp.common.calc.dti import compute_dti_ratio
from mortgage_mcp.common.calc.ltv import compute_ltv_cltv
from mortgage_mcp.common.errors.app_errors import VALIDATION_ERROR, ToolError
from mortgage_mcp.common.types.enums import DtiMethod, EligibilityStatus, LoanType
from mortgage_mcp.tools.check_borrower_eligibility.rules_engine.evaluator import default_policy_refs, evaluate_rules
from mortgage_mcp.tools.check_borrower_eligibility.rules_engine.loader import load_rules
from mortgage_mcp.tools.check_borrower_eligibility.schemas import CheckBorrowerEligibilityInput

RULESET_VERSION = "uw-rules@2026.05.01"


def _data_dir() -> Path:
    return Path(__file__).resolve().parent / "data"


def _load_json(name: str) -> dict:
    path = _data_dir() / name
    return json.loads(path.read_text(encoding="utf-8"))


def _find_borrower(borrower_id: str) -> dict:
    data = _load_json("borrowers.json")
    for b in data["borrowers"]:
        if b["borrower_id"] == borrower_id:
            return b
    raise ToolError(VALIDATION_ERROR, f"borrower_id not found in eligibility mock data: {borrower_id}")


def _find_application(application_id: str, borrower_id: str) -> dict:
    data = _load_json("loan_applications.json")
    for a in data["applications"]:
        if a["application_id"] == application_id and a["borrower_id"] == borrower_id:
            return a
    raise ToolError(
        VALIDATION_ERROR,
        f"application_id {application_id} not found for borrower_id {borrower_id} in eligibility mock data",
    )


async def run_check_borrower_eligibility(raw: dict) -> dict:
    correlation_id = str(uuid.uuid4())
    try:
        payload = CheckBorrowerEligibilityInput.model_validate(raw)
    except Exception as exc:  # noqa: BLE001
        raise ToolError(VALIDATION_ERROR, str(exc)) from exc

    try:
        lt = LoanType(payload.loan_type_normalized)
    except ValueError as exc:
        raise ToolError(VALIDATION_ERROR, f"Unsupported loan_type: {payload.loan_type}") from exc

    borrower = _find_borrower(payload.borrower_id)
    application = _find_application(payload.application_id, payload.borrower_id)

    gross_monthly_income = float(borrower["annual_income"]) / 12.0
    dti, dti_components = compute_dti_ratio(
        gross_monthly_income=gross_monthly_income,
        monthly_housing_payment=float(application["monthly_pitia"]),
        monthly_non_mortgage_debts=float(borrower["monthly_non_housing_debts"]),
        method=DtiMethod.BACK_END,
    )
    ltv, cltv, ltv_components = compute_ltv_cltv(
        loan_amount=float(application["loan_amount"]),
        appraised_value=float(application["appraised_value"]),
        subordinate_financing=float(application.get("subordinate_financing", 0)),
    )

    rules = load_rules(lt)
    eligible, failed_rules, reasons, risk = evaluate_rules(
        rules=rules,
        loan_type=lt,
        credit_score=int(borrower["credit_score"]),
        dti=dti,
        ltv=ltv,
        reserves_months=float(borrower["reserves_months"]),
    )

    has_fail = any(fr.severity == "FAIL" for fr in failed_rules)
    has_warn = any(fr.severity == "WARN" for fr in failed_rules)

    if has_fail:
        status = EligibilityStatus.DECLINED
    elif has_warn:
        status = EligibilityStatus.REFER_TO_UNDERWRITER
    else:
        status = EligibilityStatus.APPROVED

    dti_explanation = (
        f"Back-end DTI is {dti}%, compared to a mock {lt.value} maximum of {rules.max_dti}% "
        f"for ruleset {RULESET_VERSION}."
    )
    ltv_explanation = (
        f"LTV is {ltv}% (CLTV {cltv}%) against a mock maximum purchase LTV of {rules.max_ltv_purchase}%."
    )
    if lt == LoanType.CONVENTIONAL and rules.pmi_ltv_threshold is not None and ltv > rules.pmi_ltv_threshold:
        ltv_explanation += (
            f" PMI is likely required because LTV exceeds the mock conventional threshold of "
            f"{rules.pmi_ltv_threshold}%."
        )

    policy_refs = [p.model_dump() for p in default_policy_refs(lt)]

    recommended_products: list[str] = []
    if eligible:
        if lt == LoanType.CONVENTIONAL:
            recommended_products = ["30_YEAR_FIXED", "7_6_SOFR_ARM"]
        elif lt == LoanType.FHA:
            recommended_products = ["FHA_30_YEAR_FIXED"]
        elif lt == LoanType.VA:
            recommended_products = ["VA_30_YEAR_FIXED"]
        else:
            recommended_products = ["JUMBO_30_YEAR_FIXED"]

    return {
        "success": True,
        "tool": "check_borrower_eligibility",
        "correlation_id": correlation_id,
        "eligible": eligible,
        "status": status.value,
        "dti_ratio": dti,
        "ltv_ratio": ltv,
        "cltv_ratio": cltv,
        "risk_level": risk.value,
        "dti_explanation": dti_explanation,
        "ltv_explanation": ltv_explanation,
        "policy_references": policy_refs,
        "reasons": reasons,
        "failed_rules": [fr.model_dump() for fr in failed_rules],
        "recommended_products": recommended_products,
        "ruleset_version": RULESET_VERSION,
        "components": {"dti": dti_components, "ltv": ltv_components},
    }
