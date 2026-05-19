"""MCP references: mortgage_max_affordable_loan_amount"""

from __future__ import annotations

from pydantic import BaseModel, Field


class MaxAffordableLoanInput(BaseModel):
    gross_monthly_income: float = Field(..., gt=0)
    monthly_non_mortgage_debts: float = Field(default=0, ge=0)
    target_dti_percent: float = Field(default=45.0, gt=0, le=65)
    annual_interest_rate: float = Field(..., ge=0, le=30)
    term_years: int = Field(default=30, ge=1, le=40)
    monthly_escrow: float = Field(default=0, ge=0, description="Taxes + insurance + HOA (non-P&I).")
    loan_type: str = Field(default="CONVENTIONAL")


class MaxAffordableLoanOutput(BaseModel):
    success: bool = True
    tool: str = "mortgage_max_affordable_loan_amount"
    correlation_id: str
    max_total_housing_payment: float
    max_principal_and_interest: float
    max_loan_amount: float
    assumed_monthly_pmi: float
    target_dti_percent: float
    explanation: str
    ruleset_version: str
