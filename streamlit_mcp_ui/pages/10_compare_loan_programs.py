"""
MCP references: mortgage_compare_loan_programs (MCP tool page only)
"""

from __future__ import annotations

import streamlit as st

from mcp_client import call_mcp_tool
from ui_helpers import (
    connection_sidebar,
    init_page,
    render_page_header,
    show_compare_programs_result,
    show_generic_exception,
)

init_page(title="Compare loan programs", icon="⚖️")

connection_sidebar(page_key="compare")

render_page_header(
    title="Compare loan programs",
    subtitle="Side-by-side mock CONVENTIONAL, FHA, VA, and JUMBO thresholds for one borrower scenario.",
)

PAIR_ALEX = ("BRW-10001", "APP-50021", "Alex Rivera")
PAIR_JORDAN = ("BRW-10002", "APP-50022", "Jordan Lee")

scenario = st.radio(
    "Demo persona",
    options=[PAIR_ALEX, PAIR_JORDAN],
    format_func=lambda x: x[2],
    horizontal=True,
)

if st.button("Compare programs", type="primary", use_container_width=True):
    borrower_id, application_id, _ = scenario
    try:
        out = call_mcp_tool(
            "mortgage_compare_loan_programs",
            {"borrower_id": borrower_id, "application_id": application_id},
        )
        show_compare_programs_result(out)
    except Exception as exc:  # noqa: BLE001
        show_generic_exception(exc)
