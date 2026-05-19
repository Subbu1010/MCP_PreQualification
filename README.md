# Mortgage Eligibility & Prequalification MCP Server

<!--
MCP references: mortgage_calculate_dti, mortgage_calculate_ltv, mortgage_estimate_monthly_payment,
                 mortgage_calculate_reserves, mortgage_max_affordable_loan_amount,
                 mortgage_check_borrower_eligibility, mortgage_compare_loan_programs,
                 mortgage_recommend_loan_products, mortgage_generate_prequal_summary,
                 mortgage_search_mortgage_policy, mortgage_explain_eligibility_decision
-->

Enterprise-style **Model Context Protocol** server for mortgage **prequalification** simulations: DTI/LTV math, monthly payment and affordability, reserves, mock eligibility, program comparison, product recommendations, consolidated prequal packets, FAISS policy search, and Gemini-backed (or offline mock) explanations.

All MCP tools are registered with the `mortgage_` prefix and declared via `@mcp.tool(...)` with `ToolAnnotations(title="mortgage", readOnlyHint=True)`.

## Requirements

- Python **3.12+** (use `py -3.12` on Windows or a 3.12 virtualenv)
- Optional: copy `.env.sample` to `.env` and set `GOOGLE_API_KEY` for Gemini explanations and Google embeddings (hash fallback works offline)

## Install

From the repository root (`MCP_PreQualification/`):

```bash
pip install -e ".[dev]"
```

On Windows, if `python` points to the wrong version:

```powershell
py -3.12 -m pip install -e ".[dev]"
```

---

## Quick start (MCP server + Streamlit UI)

Use **two terminals**. Both must target the same MCP URL: `http://127.0.0.1:8080/mcp`.

### Terminal 1 — MCP server

```powershell
cd d:\Study\MCP_PreQualification
py -3.12 -m uvicorn mortgage_mcp.main:app --host 127.0.0.1 --port 8080
```

Verify:

```powershell
Invoke-RestMethod http://127.0.0.1:8080/health
```

Expected: `{"status":"ok"}`.

### Terminal 2 — Streamlit UI

```powershell
cd d:\Study\MCP_PreQualification\streamlit_mcp_ui
pip install -r requirements.txt
$env:MCP_SERVER_URL="http://127.0.0.1:8080/mcp"
py -3.12 -m streamlit run Home.py
```

Open http://localhost:8501. In the sidebar, set **Service URL** to `http://127.0.0.1:8080/mcp` and click **Test connection** — you should see **11** tools.

### Smoke test (optional)

With the MCP server running:

```powershell
cd streamlit_mcp_ui
$env:MCP_SERVER_URL="http://127.0.0.1:8080/mcp"
py -3.12 smoke_test_mcp_from_ui.py
```

Expected: `list_tools: OK (11 tools, expected 11)` and `All tool calls succeeded`.

> **Restart after code changes:** Stop and restart Uvicorn so new or renamed tools are loaded. An old process may still expose only 6 tools.

---

## Start the MCP server (detail)

### 1. Repository root

```text
d:\Study\MCP_PreQualification
```

### 2. (Optional) Environment

```powershell
copy .env.sample .env
```

Edit `.env` only for live Gemini or Google embeddings. The server runs without API keys.

### 3. Uvicorn

**Windows:**

```powershell
py -3.12 -m uvicorn mortgage_mcp.main:app --host 127.0.0.1 --port 8080
```

**Linux / macOS:**

```bash
uvicorn mortgage_mcp.main:app --host 0.0.0.0 --port 8080
```

**Alternative** (`HOST` / `PORT` from environment):

```bash
py -3.12 -m mortgage_mcp.run
```

### Endpoints

| Check | URL | Expected |
|-------|-----|----------|
| Health | `GET http://127.0.0.1:8080/health` | `{"status":"ok"}` |
| Readiness | `GET http://127.0.0.1:8080/ready` | `{"status":"ready"}` (FAISS warmed) |
| OpenAPI | http://127.0.0.1:8080/docs | Swagger UI |
| MCP | http://127.0.0.1:8080/mcp | Streamable HTTP (`tools/list`, `tools/call`) |

### Request flow

```text
Client  →  POST /mcp  →  src/mortgage_mcp/main.py
                              └─ transport/tool_registry.py
                                   └─ tools/<name>/tool.py      (@mcp.tool)
                                        └─ tools/<name>/service.py
                                             └─ data/ | rules/ | rag/ | ai_provider/
```

Registration order in `tool_registry.py`:

1. `mortgage_calculate_dti`
2. `mortgage_calculate_ltv`
3. `mortgage_estimate_monthly_payment`
4. `mortgage_calculate_reserves`
5. `mortgage_max_affordable_loan_amount`
6. `mortgage_check_borrower_eligibility`
7. `mortgage_compare_loan_programs`
8. `mortgage_recommend_loan_products`
9. `mortgage_generate_prequal_summary`
10. `mortgage_search_mortgage_policy`
11. `mortgage_explain_eligibility_decision`

---

## How to call MCP tools

Clients use **Streamable HTTP** at `MCP_SERVER_URL` (default `http://127.0.0.1:8080/mcp`). Each call is `tools/call` with the tool **name** and a JSON **arguments** object.

### Python example

```python
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:8080/mcp"

async def main():
    async with streamable_http_client(URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "mortgage_calculate_dti",
                {
                    "gross_monthly_income": 10416.67,
                    "monthly_housing_payment": 2650,
                    "monthly_non_mortgage_debts": 950,
                    "dti_method": "BACK_END",
                    "borrower_id": "BRW-10001",
                },
            )
            print(result.structuredContent or result.content)

asyncio.run(main())
```

### Mock IDs (shared fixtures)

| Field | Sample value | Used by |
|-------|----------------|---------|
| `borrower_id` | `BRW-10001` (strong), `BRW-10002` (stressed) | eligibility, recommend, reserves, compare, summary |
| `application_id` | `APP-50021` (+ `BRW-10001`), `APP-50022` (+ `BRW-10002`) | same |
| `loan_type` | `CONVENTIONAL`, `FHA`, `VA`, `JUMBO` | eligibility, reserves, compare, summary |

Primary fixture files: `src/mortgage_mcp/tools/check_borrower_eligibility/data/borrowers.json` and `loan_applications.json`.

---

## MCP tools reference

| MCP tool name | Streamlit page | Description |
|---------------|----------------|-------------|
| `mortgage_calculate_dti` | 1 · Calculate DTI | Front-end or back-end DTI |
| `mortgage_calculate_ltv` | 2 · Calculate LTV | LTV / CLTV |
| `mortgage_estimate_monthly_payment` | 7 · Estimate payment | P&I, escrow, illustrative MI, PITIA |
| `mortgage_calculate_reserves` | 8 · Reserves | Reserves months/dollars vs guideline |
| `mortgage_max_affordable_loan_amount` | 9 · Max affordable loan | Max loan from income and target DTI |
| `mortgage_check_borrower_eligibility` | 3 · Check eligibility | Mock underwriting pre-check |
| `mortgage_compare_loan_programs` | 10 · Compare programs | CONV / FHA / VA / JUMBO matrix |
| `mortgage_recommend_loan_products` | 4 · Recommend products | Ranked mock catalog |
| `mortgage_generate_prequal_summary` | 11 · Prequal summary | Eligibility + reserves + products packet |
| `mortgage_search_mortgage_policy` | 5 · Search policy | FAISS policy retrieval |
| `mortgage_explain_eligibility_decision` | 6 · Explain decision | Narrative explanation (Gemini or mock) |

---

## Per-tool samples and code paths

### `mortgage_calculate_dti`

```json
{
  "borrower_id": "BRW-10001",
  "gross_monthly_income": 10416.67,
  "monthly_housing_payment": 2650,
  "monthly_non_mortgage_debts": 950,
  "dti_method": "BACK_END"
}
```

`dti_method`: `BACK_END` or `FRONT_END`. Optional `borrower_id` loads `tools/calculate_dti/data/borrower_overrides.json`.

**Path:** `tool.py` → `service.py` → `schemas.py` → `common/calc/dti.py`

---

### `mortgage_calculate_ltv`

```json
{
  "loan_amount": 450000,
  "appraised_value": 550000,
  "subordinate_financing": 0,
  "ltv_basis": "PURCHASE"
}
```

**Path:** `tool.py` → `service.py` → `schemas.py` → `common/calc/ltv.py`

---

### `mortgage_estimate_monthly_payment`

```json
{
  "loan_amount": 450000,
  "annual_interest_rate": 6.5,
  "term_years": 30,
  "monthly_property_tax": 450,
  "monthly_insurance": 125,
  "monthly_hoa": 0,
  "loan_type": "CONVENTIONAL",
  "appraised_value": 550000
}
```

**Path:** `tool.py` → `service.py` → `common/calc/payment.py`, `common/calc/ltv.py`

---

### `mortgage_calculate_reserves`

```json
{
  "borrower_id": "BRW-10001",
  "application_id": "APP-50021",
  "loan_type": "CONVENTIONAL"
}
```

Alternatively pass `liquid_assets_usd` + `monthly_pitia`, or `reserves_months_available` + `monthly_pitia`.

**Path:** `tool.py` → `service.py` → `data/reserves_guidelines.json`, eligibility `data/borrowers.json`, `loan_applications.json`

---

### `mortgage_max_affordable_loan_amount`

```json
{
  "gross_monthly_income": 10416.67,
  "monthly_non_mortgage_debts": 950,
  "target_dti_percent": 45.0,
  "annual_interest_rate": 6.5,
  "term_years": 30,
  "monthly_escrow": 575,
  "loan_type": "CONVENTIONAL"
}
```

**Path:** `tool.py` → `service.py` → `common/calc/payment.py`

---

### `mortgage_check_borrower_eligibility`

Approved:

```json
{
  "borrower_id": "BRW-10001",
  "application_id": "APP-50021",
  "loan_type": "CONVENTIONAL"
}
```

Declined test: `BRW-10002` + `APP-50022` + `CONVENTIONAL`.

**Path:** `tool.py` → `service.py` → `data/*.json` → `rules_engine/loader.py` → `rules/*.yaml` → `evaluator.py` → `common/calc/dti.py`, `ltv.py`

---

### `mortgage_compare_loan_programs`

```json
{
  "borrower_id": "BRW-10001",
  "application_id": "APP-50021"
}
```

Optional `programs` list (defaults to all four). Returns side-by-side eligible/status/DTI/LTV per program.

**Path:** `tool.py` → `service.py` → eligibility `data/*`, `rules_engine/*`, `common/calc/dti.py`, `ltv.py`

---

### `mortgage_recommend_loan_products`

```json
{
  "borrower_id": "BRW-10001",
  "application_id": "APP-50021",
  "fixed_only": false,
  "max_discount_points": 2.0,
  "eligible_only": true
}
```

**Path:** `tool.py` → `service.py` → `data/borrowers.json`, `loan_applications.json`, `mortgage_products.json`

---

### `mortgage_generate_prequal_summary`

```json
{
  "borrower_id": "BRW-10001",
  "application_id": "APP-50021",
  "loan_type": "CONVENTIONAL",
  "include_product_recommendations": true
}
```

Orchestrates eligibility, reserves, and (optionally) product recommendation services in one response.

**Path:** `tool.py` → `service.py` → `check_borrower_eligibility`, `calculate_reserves`, `recommend_loan_products` services

---

### `mortgage_search_mortgage_policy`

```json
{
  "query": "FHA minimum credit score for 96.5 percent LTV purchase",
  "sources": ["FHA"],
  "top_k": 3
}
```

`sources` is optional.

**Path:** `main.py` (`init_policy_index` on startup) → `tool.py` → `service.py` → `rag/retrieval.py` → `bootstrap.py` → embeddings + `vector_store/faiss_store.py` → `data/policy_documents/*`

---

### `mortgage_explain_eligibility_decision`

```json
{
  "eligibility_snapshot": {
    "eligible": false,
    "status": "DECLINED",
    "dti_ratio": 52.1,
    "ltv_ratio": 88.0,
    "loan_type": "CONVENTIONAL",
    "failed_rules": [
      {
        "rule_id": "CONV_MAX_DTI",
        "severity": "FAIL",
        "message": "DTI 52.1% > 45.0%"
      }
    ],
    "policy_references": [
      {
        "id": "FNMA-B3-6-02",
        "title": "Debt-to-income ratios (mock)",
        "excerpt_id": "CHUNK-FNMA-1182"
      }
    ]
  },
  "language": "en-US"
}
```

You may pass the JSON from `mortgage_check_borrower_eligibility`. More samples: `tools/explain_eligibility_decision/data/sample_snapshots.json`.

**Path:** `tool.py` → `service.py` → `ai_provider/vertex_gemini_provider.py` (or offline mock)

---

## Repository layout

```
src/mortgage_mcp/
  main.py                    # FastAPI app, mounts /mcp
  run.py                     # uvicorn entrypoint
  transport/tool_registry.py # registers all @mcp.tool handlers
  common/
    calc/dti.py, ltv.py, payment.py
    errors/, logging/, schemas/, types/
  tools/
    calculate_dti/
    calculate_ltv/
    estimate_monthly_payment/
    calculate_reserves/
    max_affordable_loan_amount/
    check_borrower_eligibility/
    compare_loan_programs/
    recommend_loan_products/
    generate_prequal_summary/
    search_mortgage_policy/
    explain_eligibility_decision/
streamlit_mcp_ui/            # Streamlit console (pages 1–11)
tests/
```

To add a tool: create `tools/<name>/` (`tool.py`, `service.py`, `schemas.py`), add `register_tools` in `tool_registry.py`.

To remove a tool: delete its folder and its `register_*` line in `tool_registry.py`.

## Docker / OpenShift

- `deployment/Dockerfile`
- `deployment/openshift/*.yaml`

## Tests

```bash
pytest
```

Includes service-layer tests for all eleven tools and payment amortization helpers.

## Streamlit UI

Browser console in **`streamlit_mcp_ui/`** — see `streamlit_mcp_ui/README.md` for UI-specific setup.

| Page file | MCP tool |
|-----------|----------|
| `pages/1_calculate_dti.py` | `mortgage_calculate_dti` |
| `pages/2_calculate_ltv.py` | `mortgage_calculate_ltv` |
| `pages/3_check_borrower_eligibility.py` | `mortgage_check_borrower_eligibility` |
| `pages/4_recommend_loan_products.py` | `mortgage_recommend_loan_products` |
| `pages/5_search_mortgage_policy.py` | `mortgage_search_mortgage_policy` |
| `pages/6_explain_eligibility_decision.py` | `mortgage_explain_eligibility_decision` |
| `pages/7_estimate_monthly_payment.py` | `mortgage_estimate_monthly_payment` |
| `pages/8_calculate_reserves.py` | `mortgage_calculate_reserves` |
| `pages/9_max_affordable_loan_amount.py` | `mortgage_max_affordable_loan_amount` |
| `pages/10_compare_loan_programs.py` | `mortgage_compare_loan_programs` |
| `pages/11_generate_prequal_summary.py` | `mortgage_generate_prequal_summary` |

Default form values use demo personas **Alex Rivera** (`BRW-10001` / `APP-50021`) and **Jordan Lee** (`BRW-10002` / `APP-50022`).
