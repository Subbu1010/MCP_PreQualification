"""
MCP references: search_mortgage_policy (MCP tool page only)
Purpose: Production-style form for the `search_mortgage_policy` MCP tool.
"""

from __future__ import annotations

import streamlit as st

from ui_helpers import (
    connection_sidebar,
    init_page,
    render_page_header,
    show_generic_exception,
    show_policy_search_result,
)
from mcp_client import call_mcp_tool

init_page(title="Search policy", icon="🔎")

connection_sidebar(page_key="pol")

render_page_header(
    title="Search mortgage policy library",
    subtitle="Ask in plain language. Results come from mock FHA / agency / internal excerpts—not live regulatory advice.",
)

ALL_SOURCES = ["FHA", "FNMA", "FREDDIE", "CFPB", "INTERNAL"]

with st.container(border=True):
    with st.form("pol_form"):
        q_default = "What does the FHA demo text say about credit score and 96.5 percent LTV purchases?"
        query = st.text_area("Question", value=q_default, height=110)
        scope = st.multiselect("Limit to sources (empty = all)", options=ALL_SOURCES, default=["FHA"])
        top_k = st.slider("Number of excerpts", 1, 10, 5)
        submitted = st.form_submit_button("Search", type="primary", use_container_width=True)

if submitted:
    payload: dict = {"query": query.strip(), "top_k": top_k}
    if scope:
        payload["sources"] = scope
    try:
        out = call_mcp_tool("search_mortgage_policy", payload)
        show_policy_search_result(out)
    except Exception as exc:  # noqa: BLE001
        show_generic_exception(exc)
