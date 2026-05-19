"""MCP references: mortgage_compare_loan_programs"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CompareLoanProgramsInput(BaseModel):
    borrower_id: str
    application_id: str
    programs: list[str] | None = Field(
        default=None,
        description="Defaults to CONVENTIONAL, FHA, VA, JUMBO when omitted.",
    )


class ProgramComparisonRow(BaseModel):
    program: str
    eligible: bool
    status: str
    dti_ratio: float
    ltv_ratio: float
    max_dti: float
    max_ltv_purchase: float
    min_credit_score: int
    borrower_credit_score: int
    highlights: list[str]


class CompareLoanProgramsOutput(BaseModel):
    success: bool = True
    tool: str = "mortgage_compare_loan_programs"
    correlation_id: str
    borrower_id: str
    application_id: str
    comparisons: list[ProgramComparisonRow]
    explanation: str
    ruleset_version: str
