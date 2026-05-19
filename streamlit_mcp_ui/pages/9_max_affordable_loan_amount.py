"""
MCP references: mortgage_max_affordable_loan_amount (MCP tool page only)
"""

from __future__ import annotations

import streamlit as st

from mcp_client import call_mcp_tool
from ui_helpers import (
    connection_sidebar,
    init_page,
    render_page_header,
    show_generic_exception,
    show_max_affordable_result,
)

init_page(title="Max affordable loan", icon="📊")

connection_sidebar(page_key="affordable")

render_page_header(
    title="Maximum affordable loan",
    subtitle="Reverse-solve loan amount from income, debts, and a target back-end DTI.",
)

with st.container(border=True):
    with st.form("affordable_form"):
        c1, c2 = st.columns(2)
        with c1:
            income = st.number_input("Gross monthly income", min_value=1.0, value=10_416.67, step=100.0)
            debts = st.number_input("Non-mortgage debts / mo", min_value=0.0, value=950.0, step=50.0)
            target_dti = st.number_input("Target back-end DTI (%)", min_value=1.0, max_value=65.0, value=45.0, step=0.5)
        with c2:
            rate = st.number_input("Note rate (%)", min_value=0.0, value=6.5, step=0.125)
            term = st.number_input("Term (years)", min_value=1, value=30, step=1)
            escrow = st.number_input("Monthly escrow (tax+ins+HOA)", min_value=0.0, value=575.0, step=25.0)
            loan_type = st.selectbox("Loan type (MI heuristic)", ["CONVENTIONAL", "FHA", "VA", "JUMBO"])
        submitted = st.form_submit_button("Calculate max loan", type="primary", use_container_width=True)

if submitted:
    try:
        out = call_mcp_tool(
            "mortgage_max_affordable_loan_amount",
            {
                "gross_monthly_income": income,
                "monthly_non_mortgage_debts": debts,
                "target_dti_percent": target_dti,
                "annual_interest_rate": rate,
                "term_years": int(term),
                "monthly_escrow": escrow,
                "loan_type": loan_type,
            },
        )
        show_max_affordable_result(out)
    except Exception as exc:  # noqa: BLE001
        show_generic_exception(exc)
