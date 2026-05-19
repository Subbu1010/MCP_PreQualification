"""
MCP references: check_borrower_eligibility (MCP tool page only)
Purpose: Production-style form for the `check_borrower_eligibility` MCP tool.
"""

from __future__ import annotations

import streamlit as st

from ui_helpers import (
    connection_sidebar,
    init_page,
    render_page_header,
    show_eligibility_result,
    show_generic_exception,
)
from mcp_client import call_mcp_tool

init_page(title="Check eligibility", icon="✅")

connection_sidebar(page_key="elig")

render_page_header(
    title="Check borrower eligibility (mock)",
    subtitle="Runs mock underwriting-style checks. Outcomes are for training and UAT—not a credit decision.",
)

PAIR_ALEX = ("BRW-10001", "APP-50021", "Alex Rivera — stronger profile")
PAIR_JORDAN = ("BRW-10002", "APP-50022", "Jordan Lee — stressed profile")

with st.container(border=True):
    with st.form("elig_form"):
        scenario = st.radio(
            "Demo scenario",
            options=[PAIR_ALEX, PAIR_JORDAN],
            format_func=lambda x: x[2],
            horizontal=True,
        )
        loan_type = st.selectbox(
            "Loan program",
            options=["CONVENTIONAL", "FHA", "VA", "JUMBO"],
        )
        submitted = st.form_submit_button("Run eligibility check", type="primary", use_container_width=True)

if submitted:
    borrower_id, application_id, _ = scenario
    try:
        out = call_mcp_tool(
            "mortgage_check_borrower_eligibility",
            {
                "borrower_id": borrower_id,
                "application_id": application_id,
                "loan_type": loan_type,
            },
        )
        show_eligibility_result(out)
    except Exception as exc:  # noqa: BLE001
        show_generic_exception(exc)
