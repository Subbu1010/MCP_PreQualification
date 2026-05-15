"""
MCP references: check_borrower_eligibility
Purpose: Evaluates externalized thresholds against computed metrics and returns structured failures.
"""

from __future__ import annotations

from mortgage_mcp.common.schemas.primitives import FailedRule, PolicyRef
from mortgage_mcp.common.types.enums import LoanType, RiskLevel
from mortgage_mcp.tools.check_borrower_eligibility.rules_engine.types import LoanRules


def default_policy_refs(loan_type: LoanType) -> list[PolicyRef]:
    """Mock enterprise catalog pointers (not legal advice)."""
    common = [
        PolicyRef(id="FNMA-B3-6-02", title="Debt-to-income ratios (mock)", excerpt_id="CHUNK-FNMA-1182"),
        PolicyRef(id="CFPB-RESPA-TILA-OVERVIEW", title="Disclosure concepts (mock)", excerpt_id="CHUNK-CFPB-0091"),
    ]
    if loan_type == LoanType.FHA:
        return [
            PolicyRef(id="FHA-4000.1-II-A-1", title="Credit requirements (mock)", excerpt_id="CHUNK-FHA-0441"),
            *common,
        ]
    if loan_type == LoanType.VA:
        return [
            PolicyRef(id="VA-LENDER-HB-MOCK", title="Residual income / eligibility (mock)", excerpt_id="CHUNK-VA-0007"),
            *common,
        ]
    return common


def evaluate_rules(
    *,
    rules: LoanRules,
    loan_type: LoanType,
    credit_score: int,
    dti: float,
    ltv: float,
    reserves_months: float,
    min_reserves_required: float = 2.0,
) -> tuple[bool, list[FailedRule], list[str], RiskLevel]:
    """
    Returns (eligible, failed_rules, reasons, risk_level).

    `min_reserves_required` is a simplified mock gate for owner-occupied purchase scenarios.
    """
    failed: list[FailedRule] = []
    reasons: list[str] = []

    if credit_score < rules.min_credit_score:
        failed.append(
            FailedRule(
                rule_id=f"{loan_type.name}_MIN_FICO",
                severity="FAIL",
                message=f"Credit score {credit_score} below minimum {rules.min_credit_score}",
            )
        )
    else:
        reasons.append(f"Credit score of {credit_score} meets minimum threshold for {loan_type.value}")

    if dti > rules.max_dti:
        failed.append(
            FailedRule(
                rule_id=f"{loan_type.name}_MAX_DTI",
                severity="FAIL",
                message=f"DTI {dti}% > {rules.max_dti}%",
            )
        )
    else:
        reasons.append("DTI within program limit")

    if ltv > rules.max_ltv_purchase:
        failed.append(
            FailedRule(
                rule_id=f"{loan_type.name}_MAX_LTV_PURCHASE",
                severity="FAIL",
                message=f"LTV {ltv}% > {rules.max_ltv_purchase}%",
            )
        )
    else:
        reasons.append("LTV within program maximum for purchase (mock ruleset)")

    if reserves_months < min_reserves_required:
        failed.append(
            FailedRule(
                rule_id="RESERVES_POST_CLOSE",
                severity="WARN",
                message=f"Reserves {reserves_months} months < guideline {min_reserves_required} months",
            )
        )
        reasons.append("Reserves below typical guideline — routed to manual review in mock flow")
    else:
        reasons.append("Reserves meet guideline for mock owner-occupied purchase")

    eligible = all(fr.severity != "FAIL" for fr in failed)

    risk = RiskLevel.LOW
    warn_count = sum(1 for fr in failed if fr.severity == "WARN")
    if not eligible or dti > rules.max_dti - 5 or ltv > rules.max_ltv_purchase - 3:
        risk = RiskLevel.HIGH if not eligible else RiskLevel.MODERATE
    elif warn_count or dti > 40 or ltv > (rules.pmi_ltv_threshold or 80) + 1:
        risk = RiskLevel.MODERATE

    return eligible, failed, reasons, risk
