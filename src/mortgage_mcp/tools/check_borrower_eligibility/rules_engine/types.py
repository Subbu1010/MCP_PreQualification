"""
MCP references: check_borrower_eligibility
Purpose: Declares the YAML shape for externalized mortgage rules (no hardcoded thresholds in Python).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class LoanRules(BaseModel):
    program: str
    min_credit_score: int = Field(..., ge=300, le=850)
    max_dti: float = Field(..., gt=0, le=100)
    max_ltv_purchase: float = Field(..., gt=0, le=100)
    pmi_ltv_threshold: float | None = Field(default=None, description="Conventional PMI threshold (LTV percent).")
    notes: str | None = None
