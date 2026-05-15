"""
MCP references: check_borrower_eligibility
Purpose: Loads per-program YAML rules from this MCP tool folder only (safe to delete with the tool).
"""

from __future__ import annotations

from pathlib import Path

import yaml

from mortgage_mcp.common.types.enums import LoanType
from mortgage_mcp.tools.check_borrower_eligibility.rules_engine.types import LoanRules


def rules_dir() -> Path:
    return Path(__file__).resolve().parent / "rules"


def load_rules(loan_type: LoanType) -> LoanRules:
    path = rules_dir() / f"{loan_type.name.lower()}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Missing rules file for {loan_type}: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return LoanRules.model_validate(raw)
