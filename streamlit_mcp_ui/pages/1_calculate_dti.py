"""
MCP references: calculate_dti (MCP tool page only)
Purpose: Production-style form for the `calculate_dti` MCP tool.
"""

from __future__ import annotations

import streamlit as st

from ui_helpers import (
    connection_sidebar,
    init_page,
    render_page_header,
    show_dti_result,
    show_generic_exception,
)
from mcp_client import call_mcp_tool

init_page(title="Calculate DTI", icon="📊")

connection_sidebar(page_key="dti")

render_page_header(
    title="Calculate debt-to-income (DTI)",
    subtitle="Compare total monthly housing and other debts to gross monthly income. Optional demo borrower applies small mock adjustments.",
)

with st.container(border=True):
    with st.form("dti_form"):
        st.markdown("##### Borrower (optional)")
        borrower = st.selectbox(
            "Demo borrower",
            options=["(none — numbers only)", "Alex Rivera (BRW-10001)", "Jordan Lee (BRW-10002)"],
            help="Selecting a persona may apply mock overlays used in demos.",
        )
        st.markdown("##### Monthly amounts (USD)")
        c1, c2 = st.columns(2)
        with c1:
            gross = st.number_input(
                "Gross monthly income",
                min_value=0.0,
                value=10416.67,
                step=100.0,
            )
            housing = st.number_input(
                "Total housing payment (PITIA)",
                min_value=0.0,
                value=2650.0,
                step=50.0,
            )
        with c2:
            other_debts = st.number_input(
                "Other monthly debts",
                min_value=0.0,
                value=950.0,
                step=25.0,
            )
            method = st.selectbox(
                "DTI method",
                options=["BACK_END", "FRONT_END"],
                format_func=lambda x: "Back-end (housing + other debts)" if x == "BACK_END" else "Front-end (housing only)",
            )
        submitted = st.form_submit_button("Run DTI check", type="primary", use_container_width=True)

if submitted:
    bid = None
    if borrower.startswith("Alex"):
        bid = "BRW-10001"
    elif borrower.startswith("Jordan"):
        bid = "BRW-10002"
    payload = {
        "gross_monthly_income": gross,
        "monthly_housing_payment": housing,
        "monthly_non_mortgage_debts": other_debts,
        "dti_method": method,
    }
    if bid:
        payload["borrower_id"] = bid
    try:
        out = call_mcp_tool("calculate_dti", payload)
        show_dti_result(out)
    except Exception as exc:  # noqa: BLE001
        show_generic_exception(exc)
