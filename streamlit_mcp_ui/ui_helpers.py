"""
MCP references: (Streamlit UI helpers — not MCP server code)
Purpose: Global CSS injection, branded chrome, page headers, and structured result panels for production UI.
"""

from __future__ import annotations

import html
import os
from pathlib import Path
from typing import Any

import streamlit as st

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

_ASSETS_DIR = Path(__file__).resolve().parent / "assets"
_CSS_PATH = _ASSETS_DIR / "app.css"


def inject_global_styles() -> None:
    """Load `assets/app.css` once per run; must be called early on every page."""
    try:
        css = _CSS_PATH.read_text(encoding="utf-8")
    except OSError:
        css = "/* app.css missing */"
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def init_page(*, title: str, icon: str = "🏦", layout: str = "wide") -> None:
    st.set_page_config(page_title=title, page_icon=icon, layout=layout, initial_sidebar_state="expanded")
    inject_global_styles()


def render_page_header(*, title: str, subtitle: str, kicker: str = "Mortgage prequalification lab") -> None:
    """Enterprise-style page title block (HTML + escaped strings)."""
    st.markdown(
        f'<div class="mm-page-header">'
        f'<p class="mm-page-kicker">{html.escape(kicker)}</p>'
        f"<h1>{html.escape(title)}</h1>"
        f'<p class="mm-page-desc">{html.escape(subtitle)}</p>'
        f"</div>",
        unsafe_allow_html=True,
    )


def connection_sidebar(*, page_key: str) -> None:
    """Branded sidebar with MCP endpoint configuration."""
    st.sidebar.markdown(
        '<div class="mm-sidebar-brand">'
        '<p class="mm-sidebar-product">Mortgage MCP</p>'
        '<p class="mm-sidebar-sub">Prequal test console</p>'
        "</div>",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("### Connection")
    default_url = os.environ.get("MCP_SERVER_URL", "http://127.0.0.1:8080/mcp")
    url = st.sidebar.text_input(
        "Service URL",
        value=default_url,
        key=f"mcp_url_{page_key}",
        help="Full URL ending in /mcp (from your IT runbook).",
    )
    if url:
        os.environ["MCP_SERVER_URL"] = url.rstrip("/")

    st.sidebar.markdown(
        "<p class='mm-sidebar-hint'>Use <strong>Test connection</strong> before running checks.</p>",
        unsafe_allow_html=True,
    )
    if st.sidebar.button("Test connection", key=f"ping_{page_key}", use_container_width=True):
        try:
            from mcp_client import list_tools_sync

            tools = list_tools_sync()
            st.sidebar.success(f"{len(tools)} tools available.")
            st.sidebar.caption(", ".join(tools))
        except Exception as exc:  # noqa: BLE001
            st.sidebar.error("Unreachable host or path.")
            with st.sidebar.expander("Diagnostics"):
                st.code(str(exc))


def _technical_payload(data: Any) -> None:
    with st.expander("Technical — full JSON response", expanded=False):
        st.json(data)


def render_tool_error(out: dict[str, Any]) -> bool:
    if out.get("success") is False or out.get("code"):
        code = out.get("code", "ERROR")
        msg = out.get("message", "The service could not complete this request.")
        st.error(f"**{html.escape(str(code))}** — {html.escape(str(msg))}")
        _technical_payload(out)
        return True
    return False


def show_dti_result(out: dict[str, Any]) -> None:
    if render_tool_error(out):
        return
    with st.container(border=True):
        st.success("Debt-to-income calculated.")
        c1, c2, c3 = st.columns(3)
        c1.metric("DTI ratio", f"{out.get('dti_ratio', '—')}%")
        c2.metric("Method", str(out.get("dti_method", "—")).replace("_", " ").title())
        c3.metric("Rules version", str(out.get("ruleset_version", "—"))[:20])
        st.divider()
        st.markdown("##### What this means")
        st.info(out.get("explanation", "—"))
        comps = out.get("components") or {}
        if comps:
            st.markdown("##### Numbers used")
            rows = [
                {
                    "Item": k,
                    "Amount (USD)": f"{float(v):,.2f}" if isinstance(v, (int, float)) else str(v),
                }
                for k, v in comps.items()
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)
        warns = out.get("warnings") or []
        for w in warns:
            st.warning(w)
        _technical_payload(out)


def show_ltv_result(out: dict[str, Any]) -> None:
    if render_tool_error(out):
        return
    with st.container(border=True):
        st.success("Loan-to-value calculated.")
        c1, c2, c3 = st.columns(3)
        c1.metric("LTV", f"{out.get('ltv_ratio', '—')}%")
        c2.metric("CLTV", f"{out.get('cltv_ratio', '—')}%")
        c3.metric("Rules version", str(out.get("ruleset_version", "—"))[:24])
        st.divider()
        st.markdown("##### Summary")
        st.info(out.get("explanation", "—"))
        hint = out.get("pmi_required_hint")
        if hint:
            st.markdown("##### Private mortgage insurance (PMI)")
            st.warning(hint)
        _technical_payload(out)


def show_eligibility_result(out: dict[str, Any]) -> None:
    if render_tool_error(out):
        return
    with st.container(border=True):
        eligible = bool(out.get("eligible"))
        status = str(out.get("status", "—"))
        if eligible and status == "APPROVED":
            st.success(
                f"**Outcome:** {html.escape(status)} — appears eligible under the mock ruleset (demo only)."
            )
        elif status == "REFER_TO_UNDERWRITER":
            st.warning(f"**Outcome:** {html.escape(status)} — manual review recommended.")
        else:
            st.error(f"**Outcome:** {html.escape(status)} — not eligible under the mock ruleset.")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("DTI", f"{out.get('dti_ratio', '—')}%")
        c2.metric("LTV", f"{out.get('ltv_ratio', '—')}%")
        c3.metric("Risk", str(out.get("risk_level", "—")))
        c4.metric("Rules", str(out.get("ruleset_version", "—"))[:14])

        st.divider()
        st.markdown("##### Summary")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Income vs debts (DTI)**")
            st.caption(out.get("dti_explanation", "—"))
        with col_b:
            st.markdown("**Loan vs value (LTV)**")
            st.caption(out.get("ltv_explanation", "—"))

        reasons = out.get("reasons") or []
        if reasons:
            st.markdown("##### Key points")
            for r in reasons:
                st.markdown(f"- {r}")

        failed = out.get("failed_rules") or []
        if failed:
            st.markdown("##### Rule checks")
            st.dataframe(failed, use_container_width=True, hide_index=True)

        refs = out.get("policy_references") or []
        if refs:
            st.markdown("##### Policy references (mock)")
            st.dataframe(refs, use_container_width=True, hide_index=True)

        products = out.get("recommended_products") or []
        if products:
            st.markdown("##### Illustrative product codes")
            st.write(", ".join(str(p) for p in products))

        _technical_payload(out)


def show_recommendations_result(out: dict[str, Any]) -> None:
    if render_tool_error(out):
        return
    with st.container(border=True):
        st.success("Recommendations generated.")
        echo = out.get("inputs_echo") or {}
        st.caption(
            f"Scenario context — DTI **{echo.get('dti_ratio', '—')}%**, LTV **{echo.get('ltv_ratio', '—')}%**, "
            f"**{echo.get('loan_type', '—')}**."
        )
        rows = out.get("recommendations") or []
        if not rows:
            st.info("No products returned for this combination.")
        else:
            display = []
            for r in rows:
                stub = r.get("estimated_note_rate_apr_stub") or {}
                display.append(
                    {
                        "Product": r.get("product_code"),
                        "Match": r.get("score"),
                        "Rationale": r.get("rationale", ""),
                        "Note %": stub.get("note_rate"),
                        "APR %": stub.get("apr"),
                    }
                )
            st.dataframe(display, use_container_width=True, hide_index=True)
            st.caption("Illustrative only — not a Loan Estimate or offer.")
        _technical_payload(out)


def show_policy_search_result(out: dict[str, Any]) -> None:
    if render_tool_error(out):
        return
    with st.container(border=True):
        st.success("Policy excerpts retrieved.")
        st.caption(f"Corpus index: **{out.get('index_version', '—')}**")
        hits = out.get("hits") or []
        if not hits:
            st.info("No excerpts — refine the question or widen sources.")
        else:
            rows = []
            for h in hits:
                cit = h.get("citation") or {}
                rows.append(
                    {
                        "Score": h.get("score"),
                        "Document": h.get("document_id"),
                        "Section": h.get("section"),
                        "Excerpt": (h.get("snippet") or "")[:380]
                        + ("…" if len(str(h.get("snippet", ""))) > 380 else ""),
                        "Effective": cit.get("effective_date"),
                    }
                )
            st.dataframe(rows, use_container_width=True, hide_index=True)
        _technical_payload(out)


def show_explain_result(out: dict[str, Any]) -> None:
    if render_tool_error(out):
        return
    with st.container(border=True):
        st.success("Explanation generated.")
        st.caption(f"Model reference: `{html.escape(str(out.get('model_id', '—')))}`")
        st.markdown("##### Narrative (advisory)")
        st.write(out.get("narrative", "—"))
        st.markdown("##### Structured summary")
        st.json(out.get("structured_summary") or {})
        cites = out.get("citations_used") or []
        if cites:
            st.markdown("##### Citations")
            st.dataframe(cites, use_container_width=True, hide_index=True)
        if out.get("disclaimer"):
            st.warning(out["disclaimer"])
        _technical_payload(out)


def show_payment_estimate_result(out: dict[str, Any]) -> None:
    if render_tool_error(out):
        return
    with st.container(border=True):
        st.success("Monthly payment estimated.")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total PITIA", f"${out.get('total_monthly_payment', 0):,.2f}")
        c2.metric("P&I", f"${out.get('principal_and_interest', 0):,.2f}")
        c3.metric("Escrow", f"${out.get('monthly_escrow', 0):,.2f}")
        c4.metric("MI (mock)", f"${out.get('monthly_pmi', 0):,.2f}")
        st.info(out.get("explanation", "—"))
        if out.get("ltv_ratio") is not None:
            st.caption(f"Implied LTV: **{out.get('ltv_ratio')}%**")
        _technical_payload(out)


def show_reserves_result(out: dict[str, Any]) -> None:
    if render_tool_error(out):
        return
    with st.container(border=True):
        meets = bool(out.get("meets_guideline"))
        st.success("Reserves evaluated.") if meets else st.warning("Reserves below mock guideline.")
        c1, c2, c3 = st.columns(3)
        c1.metric("Required months", out.get("required_months", "—"))
        c2.metric("Available months", out.get("available_months", "—"))
        c3.metric("Required $", f"${out.get('required_dollars', 0):,.0f}")
        st.info(out.get("explanation", "—"))
        _technical_payload(out)


def show_max_affordable_result(out: dict[str, Any]) -> None:
    if render_tool_error(out):
        return
    with st.container(border=True):
        st.success("Maximum affordable loan estimated.")
        c1, c2, c3 = st.columns(3)
        c1.metric("Max loan", f"${out.get('max_loan_amount', 0):,.0f}")
        c2.metric("Max housing / mo", f"${out.get('max_total_housing_payment', 0):,.2f}")
        c3.metric("Target DTI", f"{out.get('target_dti_percent', '—')}%")
        st.info(out.get("explanation", "—"))
        _technical_payload(out)


def show_compare_programs_result(out: dict[str, Any]) -> None:
    if render_tool_error(out):
        return
    with st.container(border=True):
        st.success("Program comparison ready.")
        st.caption(out.get("explanation", "—"))
        rows = out.get("comparisons") or []
        if rows:
            display = [
                {
                    "Program": r.get("program"),
                    "Eligible": r.get("eligible"),
                    "Status": r.get("status"),
                    "DTI %": r.get("dti_ratio"),
                    "LTV %": r.get("ltv_ratio"),
                    "Max DTI": r.get("max_dti"),
                    "Max LTV": r.get("max_ltv_purchase"),
                    "FICO": r.get("borrower_credit_score"),
                }
                for r in rows
            ]
            st.dataframe(display, use_container_width=True, hide_index=True)
        _technical_payload(out)


def show_prequal_summary_result(out: dict[str, Any]) -> None:
    if render_tool_error(out):
        return
    with st.container(border=True):
        st.success("Prequalification summary generated.")
        summary = out.get("summary") or {}
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Status", str(summary.get("status", "—")))
        c2.metric("DTI", f"{summary.get('dti_ratio', '—')}%")
        c3.metric("LTV", f"{summary.get('ltv_ratio', '—')}%")
        c4.metric("Risk", str(summary.get("risk_level", "—")))
        st.info(out.get("explanation", "—"))
        st.markdown("##### Packet")
        st.json(summary)
        _technical_payload(out)


def show_generic_exception(exc: BaseException) -> None:
    with st.container(border=True):
        st.error(
            "The mortgage service could not be reached. Confirm the URL with IT, VPN, and firewall rules, then retry."
        )
        with st.expander("Diagnostics"):
            st.exception(exc)
