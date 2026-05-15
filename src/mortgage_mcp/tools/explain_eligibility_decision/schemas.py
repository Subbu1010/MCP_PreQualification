"""
MCP references: explain_eligibility_decision
Purpose: Pydantic validation for the eligibility snapshot passed into the explanation MCP tool.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from mortgage_mcp.common.schemas.primitives import FailedRule, PolicyRef


class EligibilitySnapshot(BaseModel):
    eligible: bool
    status: str
    dti_ratio: float | None = None
    ltv_ratio: float | None = None
    loan_type: str | None = None
    failed_rules: list[FailedRule] = Field(default_factory=list)
    policy_references: list[PolicyRef] = Field(default_factory=list)

    @model_validator(mode="after")
    def declined_requires_fail_rules(self) -> EligibilitySnapshot:
        if not self.eligible:
            if not self.failed_rules or not any(fr.severity == "FAIL" for fr in self.failed_rules):
                raise ValueError(
                    "When eligible=false, failed_rules must include at least one entry with severity=FAIL"
                )
        return self
