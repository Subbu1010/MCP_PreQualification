"""MCP references: mortgage_calculate_reserves"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class CalculateReservesInput(BaseModel):
    loan_type: str
    borrower_id: str | None = None
    application_id: str | None = None
    liquid_assets_usd: float | None = Field(default=None, ge=0)
    monthly_pitia: float | None = Field(default=None, gt=0)
    reserves_months_available: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _require_source(self) -> CalculateReservesInput:
        has_borrower = self.borrower_id and self.application_id
        has_manual = self.liquid_assets_usd is not None and self.monthly_pitia is not None
        has_months = self.reserves_months_available is not None and self.monthly_pitia is not None
        if not (has_borrower or has_manual or has_months):
            raise ValueError(
                "Provide borrower_id+application_id, or liquid_assets_usd+monthly_pitia, "
                "or reserves_months_available+monthly_pitia"
            )
        return self


class CalculateReservesOutput(BaseModel):
    success: bool = True
    tool: str = "mortgage_calculate_reserves"
    correlation_id: str
    loan_type: str
    required_months: float
    available_months: float
    required_dollars: float
    available_dollars: float
    meets_guideline: bool
    explanation: str
    ruleset_version: str
