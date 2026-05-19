"""
MCP references: mortgage_estimate_monthly_payment (MCP tool page only)
"""

from __future__ import annotations

import streamlit as st

from mcp_client import call_mcp_tool
from ui_helpers import (
    connection_sidebar,
    init_page,
    render_page_header,
    show_generic_exception,
    show_payment_estimate_result,
)

init_page(title="Estimate monthly payment", icon="💵")

connection_sidebar(page_key="payment")

render_page_header(
    title="Estimate monthly payment",
    subtitle="P&I, escrow, and illustrative mortgage insurance for a mock PITIA.",
)

with st.container(border=True):
    with st.form("payment_form"):
        st.markdown("##### Loan terms")
        c1, c2 = st.columns(2)
        with c1:
            loan = st.number_input("Loan amount", min_value=0.0, value=450_000.0, step=5_000.0)
            rate = st.number_input("Note rate (%)", min_value=0.0, value=6.5, step=0.125)
            term = st.number_input("Term (years)", min_value=1, value=30, step=1)
        with c2:
            value = st.number_input("Appraised value (optional, for LTV/MI)", min_value=0.0, value=550_000.0, step=5_000.0)
            loan_type = st.selectbox("Loan type", ["CONVENTIONAL", "FHA", "VA", "JUMBO"])
        st.markdown("##### Monthly escrow (USD)")
        e1, e2, e3 = st.columns(3)
        with e1:
            tax = st.number_input("Property tax", min_value=0.0, value=450.0, step=25.0)
        with e2:
            ins = st.number_input("Insurance", min_value=0.0, value=125.0, step=25.0)
        with e3:
            hoa = st.number_input("HOA", min_value=0.0, value=0.0, step=25.0)
        submitted = st.form_submit_button("Estimate payment", type="primary", use_container_width=True)

if submitted:
    payload = {
        "loan_amount": loan,
        "annual_interest_rate": rate,
        "term_years": int(term),
        "monthly_property_tax": tax,
        "monthly_insurance": ins,
        "monthly_hoa": hoa,
        "loan_type": loan_type,
    }
    if value > 0:
        payload["appraised_value"] = value
    try:
        out = call_mcp_tool("mortgage_estimate_monthly_payment", payload)
        show_payment_estimate_result(out)
    except Exception as exc:  # noqa: BLE001
        show_generic_exception(exc)
