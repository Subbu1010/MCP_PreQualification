"""
MCP references: (Streamlit UI smoke test — not a production page)
Purpose: Headless check that the same MCP calls used by Streamlit pages succeed against a running server.
Run from `streamlit_mcp_ui/`:  MCP_SERVER_URL=http://127.0.0.1:8080/mcp python smoke_test_mcp_from_ui.py
"""

from __future__ import annotations

import os
import sys

# Ensure this directory is importable when run as `python smoke_test_mcp_from_ui.py`
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault("MCP_SERVER_URL", "http://127.0.0.1:8080/mcp")

from mcp_client import call_mcp_tool, list_tools_sync  # noqa: E402


def main() -> None:
    url = os.environ["MCP_SERVER_URL"]
    print(f"MCP_SERVER_URL={url}")

    tools = list_tools_sync()
    print(f"list_tools: OK ({len(tools)} tools)")
    print(tools)

    checks = [
        (
            "calculate_dti",
            {
                "borrower_id": "BRW-10001",
                "gross_monthly_income": 10416.67,
                "monthly_housing_payment": 2650,
                "monthly_non_mortgage_debts": 950,
                "dti_method": "BACK_END",
            },
        ),
        (
            "calculate_ltv",
            {
                "loan_amount": 450000,
                "appraised_value": 550000,
                "subordinate_financing": 0,
                "ltv_basis": "PURCHASE",
            },
        ),
        (
            "check_borrower_eligibility",
            {
                "borrower_id": "BRW-10001",
                "application_id": "APP-50021",
                "loan_type": "CONVENTIONAL",
            },
        ),
        (
            "recommend_loan_products",
            {
                "borrower_id": "BRW-10001",
                "application_id": "APP-50021",
                "fixed_only": False,
                "max_discount_points": 2.0,
                "eligible_only": True,
            },
        ),
        (
            "search_mortgage_policy",
            {
                "query": "FHA minimum credit score for 96.5 percent LTV purchase",
                "sources": ["FHA"],
                "top_k": 3,
            },
        ),
        (
            "explain_eligibility_decision",
            {
                "eligibility_snapshot": {
                    "eligible": False,
                    "status": "DECLINED",
                    "dti_ratio": 52.1,
                    "ltv_ratio": 88.0,
                    "loan_type": "CONVENTIONAL",
                    "failed_rules": [
                        {
                            "rule_id": "CONV_MAX_DTI",
                            "severity": "FAIL",
                            "message": "DTI 52.1% > 45.0%",
                        }
                    ],
                    "policy_references": [
                        {
                            "id": "FNMA-B3-6-02",
                            "title": "Debt-to-income ratios (mock)",
                            "excerpt_id": "CHUNK-FNMA-1182",
                        }
                    ],
                },
                "language": "en-US",
            },
        ),
    ]

    for name, args in checks:
        out = call_mcp_tool(name, args)
        ok = out.get("success", True) and not out.get("code")
        status = "OK" if ok else f"CHECK: {out.get('code', out)}"
        print(f"  {name}: {status}")
        if not ok:
            print(out)
            sys.exit(1)

    print("\nAll tool calls succeeded (same payloads as Streamlit default JSON).")


if __name__ == "__main__":
    main()
