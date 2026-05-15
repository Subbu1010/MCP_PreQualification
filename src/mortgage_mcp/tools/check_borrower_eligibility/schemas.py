"""
MCP references: check_borrower_eligibility
Purpose: Request/response Pydantic models dedicated to the eligibility MCP tool.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CheckBorrowerEligibilityInput(BaseModel):
    borrower_id: str
    application_id: str
    loan_type: str = Field(..., description="CONVENTIONAL | FHA | VA | JUMBO")

    @property
    def loan_type_normalized(self) -> str:
        return self.loan_type.strip().upper()
