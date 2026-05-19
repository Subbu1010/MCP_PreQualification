"""MCP references: mortgage_estimate_monthly_payment"""

from __future__ import annotations

from pydantic import BaseModel, Field


class EstimateMonthlyPaymentInput(BaseModel):
    loan_amount: float = Field(..., ge=0)
    annual_interest_rate: float = Field(..., ge=0, le=30)
    term_years: int = Field(default=30, ge=1, le=40)
    monthly_property_tax: float = Field(default=0, ge=0)
    monthly_insurance: float = Field(default=0, ge=0)
    monthly_hoa: float = Field(default=0, ge=0)
    loan_type: str = Field(default="CONVENTIONAL")
    appraised_value: float | None = Field(default=None, gt=0)


class EstimateMonthlyPaymentOutput(BaseModel):
    success: bool = True
    tool: str = "mortgage_estimate_monthly_payment"
    correlation_id: str
    principal_and_interest: float
    monthly_pmi: float
    monthly_escrow: float
    total_monthly_payment: float
    ltv_ratio: float | None = None
    explanation: str
    ruleset_version: str
