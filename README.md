# Mortgage Eligibility & Prequalification MCP Server

<!--
MCP references: calculate_dti, calculate_ltv, check_borrower_eligibility, recommend_loan_products,
                 search_mortgage_policy, explain_eligibility_decision
Purpose: Operator documentation for running the FastAPI host and Streamable HTTP MCP endpoint.
-->

Enterprise-style **Model Context Protocol** server for mortgage **prequalification** simulations: DTI/LTV math, mock eligibility, product recommendations, FAISS policy search, and Gemini-backed (or offline mock) explanations.

## Requirements

- Python **3.12+** (required; use `py -3.12` or a 3.12 virtualenv)
- Optional: `GOOGLE_API_KEY` for Gemini `generateContent` and Google embeddings (see `.env.sample`)

## Install

```bash
pip install -e ".[dev]"
```

## Run

```bash
uvicorn mortgage_mcp.main:app --host 0.0.0.0 --port 8080
```

- **MCP (Streamable HTTP):** `http://localhost:8080/mcp` (mounted sub-application; `streamable_http_path` is `/` inside the mount).
- **Health:** `GET /health`
- **Readiness:** `GET /ready` (warms FAISS policy index for `search_mortgage_policy`).
- **OpenAPI:** `GET /docs`

## MCP tools

| Tool | Description |
|------|-------------|
| `calculate_dti` | Back-end / front-end DTI from income and obligations |
| `calculate_ltv` | LTV / CLTV from value and liens |
| `check_borrower_eligibility` | Mock eligibility with YAML rules in-tool |
| `recommend_loan_products` | Mock product ranking (duplicated JSON fixtures) |
| `search_mortgage_policy` | FAISS retrieval over in-tool policy excerpts |
| `explain_eligibility_decision` | JSON explanation via Gemini REST or offline mock |

## Layout

- `src/mortgage_mcp/common/` — shared math, settings, logging, errors (no cross-tool imports).
- `src/mortgage_mcp/tools/<tool_name>/` — one folder per MCP tool; delete a folder and its registration line in `transport/tool_registry.py` to remove the tool.

## Docker / OpenShift

- `deployment/Dockerfile`
- `deployment/openshift/*.yaml`

## Tests

```bash
pytest
```

## Optional: Streamlit UI (separate deploy)

A **browser console** for calling every MCP tool lives in **`streamlit_mcp_ui/`** (different folder, can run on another server). See `streamlit_mcp_ui/README.md`. Set `MCP_SERVER_URL` to your MCP base URL (e.g. `https://api.example.com/mcp`).