"""MCP references: mortgage_generate_prequal_summary"""

from __future__ import annotations

import uuid

from mortgage_mcp.common.errors.app_errors import VALIDATION_ERROR, ToolError
from mortgage_mcp.tools.calculate_reserves.service import run_calculate_reserves
from mortgage_mcp.tools.check_borrower_eligibility.service import run_check_borrower_eligibility
from mortgage_mcp.tools.generate_prequal_summary.schemas import (
    GeneratePrequalSummaryInput,
    GeneratePrequalSummaryOutput,
)
from mortgage_mcp.tools.recommend_loan_products.service import run_recommend_loan_products

RULESET_VERSION = "uw-rules@2026.05.01"


async def run_generate_prequal_summary(raw: dict) -> dict:
    correlation_id = str(uuid.uuid4())
    try:
        payload = GeneratePrequalSummaryInput.model_validate(raw)
    except Exception as exc:  # noqa: BLE001
        raise ToolError(VALIDATION_ERROR, str(exc)) from exc

    eligibility = await run_check_borrower_eligibility(
        {
            "borrower_id": payload.borrower_id,
            "application_id": payload.application_id,
            "loan_type": payload.loan_type,
        }
    )
    reserves = await run_calculate_reserves(
        {
            "borrower_id": payload.borrower_id,
            "application_id": payload.application_id,
            "loan_type": payload.loan_type,
        }
    )

    recommendations: dict | None = None
    if payload.include_product_recommendations:
        recommendations = await run_recommend_loan_products(
            {
                "borrower_id": payload.borrower_id,
                "application_id": payload.application_id,
                "eligible_only": True,
            }
        )

    summary = {
        "eligible": eligibility.get("eligible"),
        "status": eligibility.get("status"),
        "dti_ratio": eligibility.get("dti_ratio"),
        "ltv_ratio": eligibility.get("ltv_ratio"),
        "cltv_ratio": eligibility.get("cltv_ratio"),
        "risk_level": eligibility.get("risk_level"),
        "reasons": eligibility.get("reasons"),
        "failed_rules": eligibility.get("failed_rules"),
        "policy_references": eligibility.get("policy_references"),
        "recommended_products": eligibility.get("recommended_products"),
        "reserves": {
            "meets_guideline": reserves.get("meets_guideline"),
            "required_months": reserves.get("required_months"),
            "available_months": reserves.get("available_months"),
        },
        "product_recommendations": (recommendations or {}).get("recommendations"),
    }

    explanation = (
        f"Prequal packet for {payload.borrower_id} / {payload.application_id} ({payload.loan_type}): "
        f"status {summary.get('status')}, DTI {summary.get('dti_ratio')}%, LTV {summary.get('ltv_ratio')}%."
    )

    out = GeneratePrequalSummaryOutput(
        correlation_id=correlation_id,
        borrower_id=payload.borrower_id,
        application_id=payload.application_id,
        loan_type=payload.loan_type.upper(),
        summary=summary,
        explanation=explanation,
        ruleset_version=RULESET_VERSION,
    )
    return out.model_dump()
