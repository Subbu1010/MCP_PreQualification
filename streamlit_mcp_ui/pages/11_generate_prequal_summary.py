"""
MCP references: mortgage_generate_prequal_summary (MCP tool page only)
"""

from __future__ import annotations

import streamlit as st

from mcp_client import call_mcp_tool
from ui_helpers import (
    connection_sidebar,
    init_page,
    render_page_header,
    show_generic_exception,
    show_prequal_summary_result,
)

init_page(title="Prequal summary", icon="📋")

connection_sidebar(page_key="prequal")

render_page_header(
    title="Generate prequalification summary",
    subtitle="One-call packet: eligibility, reserves, and product recommendations.",
)

PAIR_ALEX = ("BRW-10001", "APP-50021", "Alex Rivera")
PAIR_JORDAN = ("BRW-10002", "APP-50022", "Jordan Lee")

scenario = st.radio(
    "Demo persona",
    options=[PAIR_ALEX, PAIR_JORDAN],
    format_func=lambda x: x[2],
    horizontal=True,
)
loan_type = st.selectbox("Loan type", ["CONVENTIONAL", "FHA", "VA", "JUMBO"])
include_products = st.checkbox("Include product recommendations", value=True)

if st.button("Generate summary", type="primary", use_container_width=True):
    borrower_id, application_id, _ = scenario
    try:
        out = call_mcp_tool(
            "mortgage_generate_prequal_summary",
            {
                "borrower_id": borrower_id,
                "application_id": application_id,
                "loan_type": loan_type,
                "include_product_recommendations": include_products,
            },
        )
        show_prequal_summary_result(out)
    except Exception as exc:  # noqa: BLE001
        show_generic_exception(exc)
