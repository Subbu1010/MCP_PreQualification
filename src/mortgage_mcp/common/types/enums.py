"""
MCP references: check_borrower_eligibility, recommend_loan_products, calculate_dti, calculate_ltv
Purpose: Shared enumerations for loan programs and risk labels used in multiple MCP tool responses.
"""

from __future__ import annotations

from enum import StrEnum


class LoanType(StrEnum):
    CONVENTIONAL = "CONVENTIONAL"
    FHA = "FHA"
    VA = "VA"
    JUMBO = "JUMBO"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"


class DtiMethod(StrEnum):
    BACK_END = "BACK_END"
    FRONT_END = "FRONT_END"


class EligibilityStatus(StrEnum):
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"
    REFER_TO_UNDERWRITER = "REFER_TO_UNDERWRITER"


class PolicySource(StrEnum):
    FHA = "FHA"
    FNMA = "FNMA"
    FREDDIE = "FREDDIE"
    CFPB = "CFPB"
    INTERNAL = "INTERNAL"
