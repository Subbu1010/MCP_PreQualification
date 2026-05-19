# Mortgage Eligibility & Prequalification MCP Server

<!--
MCP references: mortgage_calculate_dti, mortgage_calculate_ltv, mortgage_check_borrower_eligibility,
                 mortgage_recommend_loan_products, mortgage_search_mortgage_policy,
                 mortgage_explain_eligibility_decision
Purpose: Operator documentation for running the FastAPI host, calling MCP tools, and tracing code paths.
-->

Enterprise-style **Model Context Protocol** server for mortgage **prequalification** simulations: DTI/LTV math, mock eligibility, product recommendations, FAISS policy search, and Gemini-backed (or offline mock) explanations.

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

## Start the MCP server

### 1. Open a terminal at the repo root

```text
d:\Study\MCP_PreQualification
```

### 2. (Optional) Configure environment

```bash
copy .env.sample .env
```

Edit `.env` only if you want live Gemini or Google embeddings. The server runs without API keys using mock/hash fallbacks.

### 3. Start Uvicorn

**Windows (recommended):**

```powershell
cd d:\Study\MCP_PreQualification
py -3.12 -m uvicorn mortgage_mcp.main:app --host 127.0.0.1 --port 8080
```

**Linux / macOS:**

```bash
cd /path/to/MCP_PreQualification
uvicorn mortgage_mcp.main:app --host 0.0.0.0 --port 8080
```

**Alternative entrypoint** (same app, reads `HOST` / `PORT` from the environment):

```bash
py -3.12 -m mortgage_mcp.run
```

Leave this terminal open while clients connect.

### 4. Verify the server is up

| Check | URL / command | Expected |
|-------|----------------|----------|
| Health | `GET http://127.0.0.1:8080/health` | `{"status":"ok"}` |
| Readiness (FAISS warmed) | `GET http://127.0.0.1:8080/ready` | `{"status":"ready"}` |
| OpenAPI | http://127.0.0.1:8080/docs | FastAPI Swagger UI |
| MCP endpoint | http://127.0.0.1:8080/mcp | Streamable HTTP MCP (used by clients) |

Quick health check (PowerShell):

```powershell
Invoke-RestMethod http://127.0.0.1:8080/health
```

### 5. Smoke-test all six tools (optional)

With the server running, from `streamlit_mcp_ui/`:

```powershell
cd streamlit_mcp_ui
$env:MCP_SERVER_URL="http://127.0.0.1:8080/mcp"
py -3.12 smoke_test_mcp_from_ui.py
```

You should see `list_tools: OK (6 tools)` and `All tool calls succeeded`.

### Endpoints summary

- **MCP (Streamable HTTP):** `http://127.0.0.1:8080/mcp` — mount path for all `tools/call` traffic
- **Health:** `GET /health`
- **Readiness:** `GET /ready` (policy FAISS index for `mortgage_search_mortgage_policy`)
- **OpenAPI:** `GET /docs`

### Request flow (all tools)

```text
Client  →  POST /mcp  →  src/mortgage_mcp/main.py
                              └─ transport/tool_registry.py  (registers tools)
                                   └─ tools/<name>/tool.py     (@mcp.tool handler)
                                        └─ tools/<name>/service.py  (business logic)
                                             └─ data/, rules/, rag/, ai_provider/  (per tool)
```

---

## How to call MCP tools

MCP clients use **Streamable HTTP** at `MCP_SERVER_URL` (default `http://127.0.0.1:8080/mcp`). Each call is `tools/call` with the tool **name** and a JSON **arguments** object.

### Python example (same client as Streamlit)

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

Or run the bundled smoke test: `streamlit_mcp_ui/smoke_test_mcp_from_ui.py`.

### Mock IDs that work across tools

| Field | Sample value | Used by |
|-------|----------------|---------|
| `borrower_id` | `BRW-10001` (approved path), `BRW-10002` (declined path) | eligibility, recommend, optional DTI |
| `application_id` | `APP-50021` (with `BRW-10001`), `APP-50022` (with `BRW-10002`) | eligibility, recommend |
| `loan_type` | `CONVENTIONAL`, `FHA`, `VA`, `JUMBO` | eligibility |

Fixture files live under each tool’s `data/` folder (see per-tool sections below).

---

## MCP tools reference

| MCP tool name | Title | Description |
|---------------|-------|-------------|
| `mortgage_calculate_dti` | Calculate DTI | Front-end or back-end DTI from income and obligations |
| `mortgage_calculate_ltv` | Calculate LTV | LTV / CLTV from loan amount, value, and subordinate financing |
| `mortgage_check_borrower_eligibility` | Check Borrower Eligibility | Mock underwriting pre-check with explainable rules |
| `mortgage_recommend_loan_products` | Recommend Loan Products | Ranked mock product catalog |
| `mortgage_search_mortgage_policy` | Search Mortgage Policy | FAISS retrieval over local policy excerpts |
| `mortgage_explain_eligibility_decision` | Explain Eligibility Decision | Narrative explanation (Gemini or offline mock) |

---

### `mortgage_calculate_dti`

**Sample arguments** (known working values from smoke test):

```json
{
  "borrower_id": "BRW-10001",
  "gross_monthly_income": 10416.67,
  "monthly_housing_payment": 2650,
  "monthly_non_mortgage_debts": 950,
  "dti_method": "BACK_END"
}
```

`dti_method`: `BACK_END` or `FRONT_END`. `borrower_id` is optional; when set, extra debts may be loaded from this tool’s mock overrides file.

**Python call:**

```python
await session.call_tool("mortgage_calculate_dti", { ... })
```

**Files invoked (in order):**

1. `src/mortgage_mcp/transport/tool_registry.py` — registers handler
2. `src/mortgage_mcp/tools/calculate_dti/tool.py` — MCP entry (`@mcp.tool`)
3. `src/mortgage_mcp/tools/calculate_dti/service.py` — `run_calculate_dti()`
4. `src/mortgage_mcp/tools/calculate_dti/schemas.py` — input/output validation
5. `src/mortgage_mcp/common/calc/dti.py` — DTI math
6. `src/mortgage_mcp/tools/calculate_dti/data/borrower_overrides.json` — optional, if `borrower_id` is sent

---

### `mortgage_calculate_ltv`

**Sample arguments:**

```json
{
  "loan_amount": 450000,
  "appraised_value": 550000,
  "subordinate_financing": 0,
  "ltv_basis": "PURCHASE"
}
```

**Python call:**

```python
await session.call_tool("mortgage_calculate_ltv", { ... })
```

**Files invoked (in order):**

1. `src/mortgage_mcp/transport/tool_registry.py`
2. `src/mortgage_mcp/tools/calculate_ltv/tool.py`
3. `src/mortgage_mcp/tools/calculate_ltv/service.py` — `run_calculate_ltv()`
4. `src/mortgage_mcp/tools/calculate_ltv/schemas.py`
5. `src/mortgage_mcp/common/calc/ltv.py` — LTV / CLTV math

---

### `mortgage_check_borrower_eligibility`

**Sample arguments** (approved scenario):

```json
{
  "borrower_id": "BRW-10001",
  "application_id": "APP-50021",
  "loan_type": "CONVENTIONAL"
}
```

**Declined scenario** (for testing): `BRW-10002` + `APP-50022` + `CONVENTIONAL`.

**Python call:**

```python
await session.call_tool("mortgage_check_borrower_eligibility", { ... })
```

**Files invoked (in order):**

1. `src/mortgage_mcp/transport/tool_registry.py`
2. `src/mortgage_mcp/tools/check_borrower_eligibility/tool.py`
3. `src/mortgage_mcp/tools/check_borrower_eligibility/service.py` — `run_check_borrower_eligibility()`
4. `src/mortgage_mcp/tools/check_borrower_eligibility/schemas.py`
5. `src/mortgage_mcp/tools/check_borrower_eligibility/data/borrowers.json`
6. `src/mortgage_mcp/tools/check_borrower_eligibility/data/loan_applications.json`
7. `src/mortgage_mcp/tools/check_borrower_eligibility/data/underwriting_rules_index.json`
8. `src/mortgage_mcp/tools/check_borrower_eligibility/rules_engine/loader.py` — loads YAML rules
9. `src/mortgage_mcp/tools/check_borrower_eligibility/rules_engine/rules/*.yaml` — e.g. `conventional.yaml`
10. `src/mortgage_mcp/tools/check_borrower_eligibility/rules_engine/evaluator.py`
11. `src/mortgage_mcp/common/calc/dti.py`, `src/mortgage_mcp/common/calc/ltv.py`

---

### `mortgage_recommend_loan_products`

**Sample arguments:**

```json
{
  "borrower_id": "BRW-10001",
  "application_id": "APP-50021",
  "fixed_only": false,
  "max_discount_points": 2.0,
  "eligible_only": true
}
```

**Python call:**

```python
await session.call_tool("mortgage_recommend_loan_products", { ... })
```

**Files invoked (in order):**

1. `src/mortgage_mcp/transport/tool_registry.py`
2. `src/mortgage_mcp/tools/recommend_loan_products/tool.py`
3. `src/mortgage_mcp/tools/recommend_loan_products/service.py` — `run_recommend_loan_products()`
4. `src/mortgage_mcp/tools/recommend_loan_products/schemas.py`
5. `src/mortgage_mcp/tools/recommend_loan_products/data/borrowers.json`
6. `src/mortgage_mcp/tools/recommend_loan_products/data/loan_applications.json`
7. `src/mortgage_mcp/tools/recommend_loan_products/data/mortgage_products.json`

---

### `mortgage_search_mortgage_policy`

**Sample arguments:**

```json
{
  "query": "FHA minimum credit score for 96.5 percent LTV purchase",
  "sources": ["FHA"],
  "top_k": 3
}
```

`sources` is optional (omit to search all loaded policy documents).

**Python call:**

```python
await session.call_tool("mortgage_search_mortgage_policy", { ... })
```

**Files invoked (in order):**

1. `src/mortgage_mcp/main.py` — on startup, `init_policy_index()` warms FAISS
2. `src/mortgage_mcp/transport/tool_registry.py`
3. `src/mortgage_mcp/tools/search_mortgage_policy/tool.py`
4. `src/mortgage_mcp/tools/search_mortgage_policy/service.py` — `run_search_mortgage_policy()`
5. `src/mortgage_mcp/tools/search_mortgage_policy/rag/retrieval.py` — `search_policy()`
6. `src/mortgage_mcp/tools/search_mortgage_policy/bootstrap.py` — index + embeddings
7. `src/mortgage_mcp/tools/search_mortgage_policy/embeddings/hash_embedding.py` or `google_embeddings.py`
8. `src/mortgage_mcp/tools/search_mortgage_policy/vector_store/faiss_store.py`
9. `src/mortgage_mcp/tools/search_mortgage_policy/data/policy_manifest.json`
10. `src/mortgage_mcp/tools/search_mortgage_policy/data/policy_documents/*` — FHA, FNMA, Freddie, CFPB, internal mocks

---

### `mortgage_explain_eligibility_decision`

**Sample arguments** (minimal declined snapshot):

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

You can also pass the JSON returned from `mortgage_check_borrower_eligibility` as `eligibility_snapshot`. More examples: `src/mortgage_mcp/tools/explain_eligibility_decision/data/sample_snapshots.json`.

**Python call:**

```python
await session.call_tool("mortgage_explain_eligibility_decision", { ... })
```

**Files invoked (in order):**

1. `src/mortgage_mcp/transport/tool_registry.py`
2. `src/mortgage_mcp/tools/explain_eligibility_decision/tool.py`
3. `src/mortgage_mcp/tools/explain_eligibility_decision/service.py` — `run_explain_eligibility_decision()`
4. `src/mortgage_mcp/tools/explain_eligibility_decision/schemas.py`
5. `src/mortgage_mcp/tools/explain_eligibility_decision/ai_provider/vertex_gemini_provider.py` — live Gemini when configured
6. Offline mock path in the same service when `GOOGLE_API_KEY` is unset

---

## Repository layout

- `src/mortgage_mcp/main.py` — FastAPI app; mounts MCP at `/mcp`
- `src/mortgage_mcp/transport/tool_registry.py` — builds FastMCP and registers all tools
- `src/mortgage_mcp/common/` — shared math, settings, logging, errors
- `src/mortgage_mcp/tools/<tool_name>/` — one folder per MCP tool (`tool.py` + `service.py` + `data/`)

To remove a tool: delete its folder and remove its `register_*` line in `tool_registry.py`.

## Docker / OpenShift

- `deployment/Dockerfile`
- `deployment/openshift/*.yaml`

## Tests

```bash
pytest
```

## Optional: Streamlit UI

A browser console for calling every MCP tool lives in **`streamlit_mcp_ui/`**. See `streamlit_mcp_ui/README.md`.

1. Start the MCP server (above) on port **8080**.
2. In another terminal:

```powershell
cd streamlit_mcp_ui
pip install -r requirements.txt
$env:MCP_SERVER_URL="http://127.0.0.1:8080/mcp"
streamlit run Home.py
```

Set **Service URL** in the sidebar to `http://127.0.0.1:8080/mcp` and use **Test connection** to list the six `mortgage_*` tools.
