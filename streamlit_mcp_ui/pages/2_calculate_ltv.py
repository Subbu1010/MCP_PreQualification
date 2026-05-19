"""
MCP references: calculate_ltv (MCP tool page only)
Purpose: Production-style form for the `calculate_ltv` MCP tool.
"""

from __future__ import annotations

import streamlit as st

from ui_helpers import (
    connection_sidebar,
    init_page,
    render_page_header,
    show_generic_exception,
    show_ltv_result,
)
from mcp_client import call_mcp_tool

init_page(title="Calculate LTV", icon="📐")

connection_sidebar(page_key="ltv")

render_page_header(
    title="Calculate loan-to-value (LTV)",
    subtitle="Loan amount compared to appraised value. CLTV includes subordinate financing when provided.",
)

with st.container(border=True):
    with st.form("ltv_form"):
        st.markdown("##### Loan & property (USD)")
        c1, c2 = st.columns(2)
        with c1:
            loan = st.number_input("Loan amount", min_value=0.0, value=450_000.0, step=5_000.0)
            value = st.number_input("Appraised value", min_value=1.0, value=550_000.0, step=5_000.0)
        with c2:
            sub = st.number_input("Subordinate / second lien", min_value=0.0, value=0.0, step=1_000.0)
            basis = st.selectbox(
                "Scenario label",
                options=["PURCHASE", "RATE_TERM_REFI", "CASH_OUT_REFI"],
                format_func=lambda x: {
                    "PURCHASE": "Purchase",
                    "RATE_TERM_REFI": "Rate / term refinance",
                    "CASH_OUT_REFI": "Cash-out refinance",
                }[x],
            )
        submitted = st.form_submit_button("Run LTV check", type="primary", use_container_width=True)

if submitted:
    try:
        out = call_mcp_tool(
            "mortgage_calculate_ltv",
            {
                "loan_amount": loan,
                "appraised_value": value,
                "subordinate_financing": sub,
                "ltv_basis": basis,
            },
        )
        show_ltv_result(out)
    except Exception as exc:  # noqa: BLE001
        show_generic_exception(exc)
