"""
MCP references: calculate_dti, calculate_ltv, check_borrower_eligibility, recommend_loan_products,
                 search_mortgage_policy, explain_eligibility_decision
Purpose: Normalized error codes returned inside MCP tool JSON payloads (no HTTP auth layer in v1).
"""

from __future__ import annotations

from typing import Any


class ToolError(Exception):
    """Raised by services when a tool should return a structured failure payload."""

    def __init__(self, code: str, message: str, *, extra: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.extra = extra or {}


VALIDATION_ERROR = "VALIDATION_ERROR"
BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
UPSTREAM_UNAVAILABLE = "UPSTREAM_UNAVAILABLE"
INTERNAL_ERROR = "INTERNAL_ERROR"
LLM_REFUSAL = "LLM_REFUSAL"
