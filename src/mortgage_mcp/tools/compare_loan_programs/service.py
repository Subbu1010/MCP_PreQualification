"""MCP references: mortgage_compare_loan_programs"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from mortgage_mcp.common.calc.dti import compute_dti_ratio
from mortgage_mcp.common.calc.ltv import compute_ltv_cltv
from mortgage_mcp.common.errors.app_errors import VALIDATION_ERROR, ToolError
from mortgage_mcp.common.types.enums import DtiMethod, EligibilityStatus, LoanType
from mortgage_mcp.tools.check_borrower_eligibility.rules_engine.evaluator import evaluate_rules
from mortgage_mcp.tools.check_borrower_eligibility.rules_engine.loader import load_rules
from mortgage_mcp.tools.compare_loan_programs.schemas import (
    CompareLoanProgramsInput,
    CompareLoanProgramsOutput,
    ProgramComparisonRow,
)

RULESET_VERSION = "uw-rules@2026.05.01"
_DEFAULT_PROGRAMS = [LoanType.CONVENTIONAL, LoanType.FHA, LoanType.VA, LoanType.JUMBO]


def _data_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "check_borrower_eligibility" / "data"


def _load_json(name: str) -> dict:
    return json.loads((_data_dir() / name).read_text(encoding="utf-8"))


async def run_compare_loan_programs(raw: dict) -> dict:
    correlation_id = str(uuid.uuid4())
    try:
        payload = CompareLoanProgramsInput.model_validate(raw)
    except Exception as exc:  # noqa: BLE001
        raise ToolError(VALIDATION_ERROR, str(exc)) from exc

    borrowers = _load_json("borrowers.json")["borrowers"]
    apps = _load_json("loan_applications.json")["applications"]
    borrower = next((b for b in borrowers if b["borrower_id"] == payload.borrower_id), None)
    application = next(
        (
            a
            for a in apps
            if a["application_id"] == payload.application_id and a["borrower_id"] == payload.borrower_id
        ),
        None,
    )
    if not borrower or not application:
        raise ToolError(VALIDATION_ERROR, "borrower_id/application_id not found in mock eligibility data")

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
    credit = int(borrower["credit_score"])
    reserves = float(borrower["reserves_months"])

    if payload.programs:
        programs: list[LoanType] = []
        for p in payload.programs:
            try:
                programs.append(LoanType(p.strip().upper()))
            except ValueError as exc:
                raise ToolError(VALIDATION_ERROR, f"Unsupported program: {p}") from exc
    else:
        programs = list(_DEFAULT_PROGRAMS)

    rows: list[ProgramComparisonRow] = []
    for lt in programs:
        rules = load_rules(lt)
        eligible, failed, reasons, _risk = evaluate_rules(
            rules=rules,
            loan_type=lt,
            credit_score=credit,
            dti=dti,
            ltv=ltv,
            reserves_months=reserves,
        )
        has_fail = any(fr.severity == "FAIL" for fr in failed)
        has_warn = any(fr.severity == "WARN" for fr in failed)
        if has_fail:
            status = EligibilityStatus.DECLINED.value
        elif has_warn:
            status = EligibilityStatus.REFER_TO_UNDERWRITER.value
        else:
            status = EligibilityStatus.APPROVED.value

        highlights = reasons[:3]
        if rules.pmi_ltv_threshold and ltv > rules.pmi_ltv_threshold:
            highlights.append(f"LTV above {rules.pmi_ltv_threshold}% PMI threshold (mock)")

        rows.append(
            ProgramComparisonRow(
                program=lt.value,
                eligible=eligible,
                status=status,
                dti_ratio=dti,
                ltv_ratio=ltv,
                max_dti=rules.max_dti,
                max_ltv_purchase=rules.max_ltv_purchase,
                min_credit_score=rules.min_credit_score,
                borrower_credit_score=credit,
                highlights=highlights,
            )
        )

    best = [r.program for r in rows if r.eligible]
    explanation = (
        f"Side-by-side mock prequal for {payload.borrower_id}/{payload.application_id} at DTI {dti}% and LTV {ltv}%. "
        f"Programs appearing eligible: {', '.join(best) if best else 'none'}."
    )

    out = CompareLoanProgramsOutput(
        correlation_id=correlation_id,
        borrower_id=payload.borrower_id,
        application_id=payload.application_id,
        comparisons=rows,
        explanation=explanation,
        ruleset_version=RULESET_VERSION,
    )
    return out.model_dump()
