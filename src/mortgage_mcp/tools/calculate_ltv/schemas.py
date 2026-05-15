"""
MCP references: calculate_ltv
Purpose: Pydantic models for the `calculate_ltv` MCP tool only.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CalculateLtvInput(BaseModel):
    loan_amount: float = Field(..., ge=0)
    appraised_value: float = Field(..., gt=0)
    subordinate_financing: float = Field(default=0, ge=0)
    ltv_basis: str = Field(default="PURCHASE", description="Illustrative label for mock pricing context.")


class CalculateLtvOutput(BaseModel):
    success: bool = True
    tool: str = "calculate_ltv"
    correlation_id: str
    ltv_ratio: float
    cltv_ratio: float
    explanation: str
    pmi_required_hint: str | None = None
    ruleset_version: str
