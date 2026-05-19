"""
MCP references: (Streamlit home — lists tools; does not implement MCP tools)
Purpose: Production-style landing view with branded hero and navigation guidance.
"""

from __future__ import annotations

import html

import streamlit as st

from ui_helpers import connection_sidebar, init_page

init_page(title="Mortgage test console", icon="🏠")

st.markdown(
    """
<div class="mm-hero">
  <div class="mm-hero-badge">Internal demo environment</div>
  <h1>Mortgage prequalification test console</h1>
  <p>Run controlled checks against the MCP mortgage service—no JSON required. Use the sidebar pages for each workflow step.</p>
</div>
""",
    unsafe_allow_html=True,
)

connection_sidebar(page_key="home")

st.markdown("### Guided workflows")
st.caption("Each page maps to one MCP tool. Results are mock data for training and UAT only.")

features = [
    ("1 · Calculate DTI", "Debt-to-income from income and monthly obligations."),
    ("2 · Calculate LTV", "Loan-to-value and combined LTV including a second lien."),
    ("3 · Check eligibility", "Mock credit, DTI, LTV, and reserve rules."),
    ("4 · Recommend products", "Illustrative product ranking for the scenario."),
    ("5 · Search policy", "Natural-language search over mock policy excerpts."),
    ("6 · Explain decision", "Narrative explanation for approve / decline outcomes."),
    ("7 · Estimate payment", "P&I, escrow, and illustrative MI for monthly PITIA."),
    ("8 · Reserves", "Post-close reserves vs program guideline months."),
    ("9 · Max affordable loan", "Reverse-solve loan from income and target DTI."),
    ("10 · Compare programs", "CONVENTIONAL vs FHA vs VA vs JUMBO matrix."),
    ("11 · Prequal summary", "One-call eligibility + reserves + products packet."),
]

cols = st.columns(4)
for i, (title, desc) in enumerate(features):
    with cols[i % 4]:
        with st.container(border=True):
            st.markdown(f"**{html.escape(title)}**")
            st.caption(desc)

st.divider()
st.info(
    "**Demo personas:** Alex Rivera (`BRW-10001`) and Jordan Lee (`BRW-10002`) with matching application IDs — "
    "no real customer data."
)
