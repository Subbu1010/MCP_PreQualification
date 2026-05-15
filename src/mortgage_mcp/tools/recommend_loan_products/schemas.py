"""
MCP references: recommend_loan_products
Purpose: Input model for the product recommendation MCP tool (isolated from other tools' schemas).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RecommendLoanProductsInput(BaseModel):
    borrower_id: str
    application_id: str
    fixed_only: bool = False
    max_discount_points: float = Field(default=99.0, ge=0)
    eligible_only: bool = True
