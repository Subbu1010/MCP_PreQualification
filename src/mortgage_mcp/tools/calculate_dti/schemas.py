"""
MCP references: calculate_dti
Purpose: Pydantic models validating inputs/outputs for the `calculate_dti` MCP tool only.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from mortgage_mcp.common.types.enums import DtiMethod


class CalculateDtiInput(BaseModel):
    borrower_id: str | None = None
    gross_monthly_income: float = Field(..., gt=0)
    monthly_housing_payment: float = Field(..., ge=0)
    monthly_non_mortgage_debts: float = Field(..., ge=0)
    dti_method: DtiMethod = DtiMethod.BACK_END

    @field_validator("dti_method", mode="before")
    @classmethod
    def coerce_method(cls, v: object) -> object:
        if isinstance(v, str):
            return v.upper()
        return v


class CalculateDtiOutput(BaseModel):
    success: bool = True
    tool: str = "calculate_dti"
    correlation_id: str
    ruleset_version: str
    dti_ratio: float
    dti_method: str
    components: dict[str, float]
    explanation: str
    warnings: list[str] = Field(default_factory=list)
