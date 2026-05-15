"""
MCP references: calculate_dti, calculate_ltv, check_borrower_eligibility, recommend_loan_products,
                 search_mortgage_policy, explain_eligibility_decision
Purpose: Minimal structured logging helper (JSON-friendly dict messages) for all MCP tool paths.
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

from mortgage_mcp.common.settings import get_settings


def configure_logging() -> None:
    """Idempotent basic logging setup for Uvicorn worker processes."""
    level = getattr(logging, get_settings().mcp_log_level.upper(), logging.INFO)
    root = logging.getLogger()
    if root.handlers:
        root.setLevel(level)
        return
    logging.basicConfig(
        level=level,
        stream=sys.stdout,
        format="%(message)s",
    )


def log_event(logger: logging.Logger, *, event: str, **fields: Any) -> None:
    """Emit one JSON line for grep-friendly structured logs."""
    payload = {"event": event, **fields}
    logger.info(json.dumps(payload, default=str))
