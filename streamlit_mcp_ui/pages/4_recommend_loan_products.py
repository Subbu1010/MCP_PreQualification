"""
MCP references: recommend_loan_products (MCP tool page only)
Purpose: Production-style form for the `recommend_loan_products` MCP tool.
"""

from __future__ import annotations

import streamlit as st

from ui_helpers import (
    connection_sidebar,
    init_page,
    render_page_header,
    show_generic_exception,
    show_recommendations_result,
)
from mcp_client import call_mcp_tool

init_page(title="Recommend products", icon="📦")

connection_sidebar(page_key="rec")

render_page_header(
    title="Recommend loan products (illustrative)",
    subtitle="Ranks mock catalog entries for the selected scenario. Not an offer, LE, or pricing commitment.",
)

PAIR_ALEX = ("BRW-10001", "APP-50021", "Alex Rivera + APP-50021")
PAIR_JORDAN = ("BRW-10002", "APP-50022", "Jordan Lee + APP-50022")

with st.container(border=True):
    with st.form("rec_form"):
        scenario = st.radio("Scenario", options=[PAIR_ALEX, PAIR_JORDAN], format_func=lambda x: x[2], horizontal=True)
        fixed_only = st.checkbox("Fixed-rate products only", value=False)
        eligible_only = st.checkbox("Apply simple mock eligibility filters", value=True)
        max_points = st.slider("Max discount points (demo)", 0.0, 5.0, 2.0, 0.25)
        submitted = st.form_submit_button("Get recommendations", type="primary", use_container_width=True)

if submitted:
    borrower_id, application_id, _ = scenario
    try:
        out = call_mcp_tool(
            "recommend_loan_products",
            {
                "borrower_id": borrower_id,
                "application_id": application_id,
                "fixed_only": fixed_only,
                "max_discount_points": max_points,
                "eligible_only": eligible_only,
            },
        )
        show_recommendations_result(out)
    except Exception as exc:  # noqa: BLE001
        show_generic_exception(exc)
