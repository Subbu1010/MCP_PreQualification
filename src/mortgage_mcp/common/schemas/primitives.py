"""
MCP references: check_borrower_eligibility, recommend_loan_products (and any tool returning money IDs)
Purpose: Small reusable Pydantic models for identifiers and structured references in tool payloads.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class PolicyRef(BaseModel):
    """Citation-style policy reference returned by eligibility and explanation tools."""

    id: str = Field(..., description="Stable policy identifier (mock enterprise catalog).")
    title: str
    excerpt_id: str | None = None


class FailedRule(BaseModel):
    """Structured underwriting rule failure."""

    rule_id: str
    severity: Literal["FAIL", "WARN"]
    message: str
