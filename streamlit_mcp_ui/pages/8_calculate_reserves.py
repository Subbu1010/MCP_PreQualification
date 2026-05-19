"""
MCP references: mortgage_calculate_reserves (MCP tool page only)
"""

from __future__ import annotations

import streamlit as st

from mcp_client import call_mcp_tool
from ui_helpers import (
    connection_sidebar,
    init_page,
    render_page_header,
    show_generic_exception,
    show_reserves_result,
)

init_page(title="Calculate reserves", icon="🏦")

connection_sidebar(page_key="reserves")

render_page_header(
    title="Calculate reserves",
    subtitle="Post-close liquid reserves vs mock program guidelines (months and dollars).",
)

PAIR_ALEX = ("BRW-10001", "APP-50021", "Alex Rivera — meets guideline")
PAIR_JORDAN = ("BRW-10002", "APP-50022", "Jordan Lee — thin reserves")

scenario = st.radio(
    "Demo persona",
    options=[PAIR_ALEX, PAIR_JORDAN],
    format_func=lambda x: x[2],
)

loan_type = st.selectbox("Loan type", ["CONVENTIONAL", "FHA", "VA", "JUMBO"])

if st.button("Run reserves check", type="primary", use_container_width=True):
    borrower_id, application_id, _ = scenario
    try:
        out = call_mcp_tool(
            "mortgage_calculate_reserves",
            {
                "borrower_id": borrower_id,
                "application_id": application_id,
                "loan_type": loan_type,
            },
        )
        show_reserves_result(out)
    except Exception as exc:  # noqa: BLE001
        show_generic_exception(exc)
