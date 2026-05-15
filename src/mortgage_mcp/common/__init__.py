"""
MCP references: calculate_dti, calculate_ltv, check_borrower_eligibility, recommend_loan_products,
                 search_mortgage_policy, explain_eligibility_decision (via shared utilities only)
Purpose: Shared, tool-agnostic utilities (math, settings, logging). MCP tool code must not import
         sibling `tools/*` packages — only this `common` layer for cross-cutting helpers.
"""
