"""MCP references: mortgage_generate_prequal_summary"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class GeneratePrequalSummaryInput(BaseModel):
    borrower_id: str
    application_id: str
    loan_type: str = "CONVENTIONAL"
    include_product_recommendations: bool = True


class GeneratePrequalSummaryOutput(BaseModel):
    success: bool = True
    tool: str = "mortgage_generate_prequal_summary"
    correlation_id: str
    borrower_id: str
    application_id: str
    loan_type: str
    summary: dict[str, Any]
    explanation: str
    ruleset_version: str
