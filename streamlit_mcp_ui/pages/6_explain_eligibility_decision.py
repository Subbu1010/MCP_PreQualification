"""
MCP references: explain_eligibility_decision (MCP tool page only)
Purpose: Production-style presets for the `explain_eligibility_decision` MCP tool.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from ui_helpers import (
    connection_sidebar,
    init_page,
    render_page_header,
    show_explain_result,
    show_generic_exception,
)
from mcp_client import call_mcp_tool

init_page(title="Explain decision", icon="💬")

connection_sidebar(page_key="expl")

render_page_header(
    title="Explain an eligibility outcome",
    subtitle="Produces a short narrative for review. Advisory only—not an underwriting credit decision.",
)

PRESET_DECLINED_JORDAN: dict[str, Any] = {
    "eligible": False,
    "status": "DECLINED",
    "dti_ratio": 72.9,
    "ltv_ratio": 88.2,
    "loan_type": "CONVENTIONAL",
    "failed_rules": [
        {
            "rule_id": "CONV_MAX_DTI",
            "severity": "FAIL",
            "message": "DTI exceeds conventional mock maximum",
        },
        {
            "rule_id": "CONV_MAX_LTV_PURCHASE",
            "severity": "FAIL",
            "message": "LTV exceeds conventional mock maximum",
        },
    ],
    "policy_references": [
        {
            "id": "FNMA-B3-6-02",
            "title": "Debt-to-income ratios (mock)",
            "excerpt_id": "CHUNK-FNMA-1182",
        }
    ],
}

PRESET_APPROVED_ALEX: dict[str, Any] = {
    "eligible": True,
    "status": "APPROVED",
    "dti_ratio": 34.5,
    "ltv_ratio": 81.8,
    "loan_type": "CONVENTIONAL",
    "failed_rules": [],
    "policy_references": [
        {
            "id": "FNMA-B3-6-02",
            "title": "Debt-to-income ratios (mock)",
            "excerpt_id": "CHUNK-FNMA-1182",
        }
    ],
}

with st.container(border=True):
    with st.form("expl_form"):
        preset = st.radio(
            "Starting point",
            options=["declined_jordan", "approved_alex", "custom"],
            format_func=lambda x: {
                "declined_jordan": "Declined — Jordan (stressed DTI/LTV)",
                "approved_alex": "Approved — Alex (within limits)",
                "custom": "Custom numbers",
            }[x],
            horizontal=True,
        )
        st.markdown("##### Custom adjustments (used when “Custom” is selected)")
        c1, c2, c3 = st.columns(3)
        with c1:
            elig = st.selectbox("Eligible flag", options=[False, True], format_func=lambda x: "Yes" if x else "No")
        with c2:
            dti = st.number_input("DTI %", min_value=0.0, max_value=100.0, value=52.1, step=0.1)
        with c3:
            ltv = st.number_input("LTV %", min_value=0.0, max_value=120.0, value=88.0, step=0.1)
        loan_type = st.selectbox("Program shown in narrative", ["CONVENTIONAL", "FHA", "VA", "JUMBO"])
        language = st.selectbox("Language", ["en-US", "en-GB"])
        submitted = st.form_submit_button("Generate explanation", type="primary", use_container_width=True)

if submitted:
    if preset == "declined_jordan":
        snap = {**PRESET_DECLINED_JORDAN}
    elif preset == "approved_alex":
        snap = {**PRESET_APPROVED_ALEX}
    else:
        status = "APPROVED" if elig else "DECLINED"
        failed: list[dict[str, str]] = []
        if not elig:
            failed = [
                {
                    "rule_id": "CUSTOM_RULE",
                    "severity": "FAIL",
                    "message": f"Mock decline at DTI {dti}% and LTV {ltv}%",
                }
            ]
        snap = {
            "eligible": elig,
            "status": status,
            "dti_ratio": dti,
            "ltv_ratio": ltv,
            "loan_type": loan_type,
            "failed_rules": failed,
            "policy_references": [
                {
                    "id": "FNMA-B3-6-02",
                    "title": "Debt-to-income ratios (mock)",
                    "excerpt_id": "CHUNK-FNMA-1182",
                }
            ],
        }
    if not snap["eligible"]:
        if not snap["failed_rules"] or not any(r.get("severity") == "FAIL" for r in snap["failed_rules"]):
            snap["failed_rules"] = [
                {
                    "rule_id": "GENERIC_FAIL",
                    "severity": "FAIL",
                    "message": "Not eligible — synthetic fail rule for demo.",
                }
            ]

    try:
        out = call_mcp_tool(
            "explain_eligibility_decision",
            {"eligibility_snapshot": snap, "language": language},
        )
        show_explain_result(out)
    except Exception as exc:  # noqa: BLE001
        show_generic_exception(exc)
