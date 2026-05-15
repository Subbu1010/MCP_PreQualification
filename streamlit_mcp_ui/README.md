# MCP references: (Streamlit UI project — documents how to run against remote MCP)
# Purpose: Operator guide for the separate Streamlit app in this folder (different deploy target than the API).

# Mortgage MCP — Streamlit console

Browser UI that calls the **Mortgage Eligibility MCP** server over **Streamable HTTP**.  
Each tool has its own page with **simple fields (no JSON)** for business testers; full JSON remains under a **Technical** expander when needed.

**Look & feel:** Theme tokens live in `.streamlit/config.toml`; layout, typography, sidebar, metrics, and tables are styled in **`assets/app.css`**, injected on every page via `ui_helpers.inject_global_styles()`.

## Layout (separate from the API codebase)

This folder is self-contained next to the main server:

```text
MCP_PreQualification/
  src/mortgage_mcp/          # FastAPI + MCP server (existing)
  streamlit_mcp_ui/          # this UI (deploy elsewhere)
    Home.py
    mcp_client.py
    ui_helpers.py
    assets/app.css
    smoke_test_mcp_from_ui.py
    pages/
    requirements.txt
```

## Requirements

- Python **3.12+**
- A running MCP server (e.g. `uvicorn mortgage_mcp.main:app --port 8080`)

## Install & run (local)

```powershell
cd streamlit_mcp_ui
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
set MCP_SERVER_URL=http://127.0.0.1:8080/mcp
streamlit run Home.py
```

Copy `.env.sample` to `.env` in this folder if you use `python-dotenv` (loaded automatically when present).

## Remote MCP server (different host)

Set the full MCP URL (including `/mcp`):

```powershell
set MCP_SERVER_URL=https://mcp-api.yourbank.internal/mcp
streamlit run Home.py
```

Or use the sidebar URL field on **Home** or each tool page (it updates `os.environ` for that session).

## Pages ↔ MCP tools

| Page | MCP tool |
|------|-----------|
| Calculate DTI | `calculate_dti` |
| Calculate LTV | `calculate_ltv` |
| Check borrower eligibility | `check_borrower_eligibility` |
| Recommend loan products | `recommend_loan_products` |
| Search mortgage policy | `search_mortgage_policy` |
| Explain eligibility decision | `explain_eligibility_decision` |

Default JSON on each page matches the **mock borrowers/applications** in the MCP server repo (`BRW-10001`, `APP-50021`, etc.).

## Docker (example)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV MCP_SERVER_URL=http://mortgage-mcp-service:8080/mcp
EXPOSE 8501
CMD ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build from **inside** `streamlit_mcp_ui/` so `Home.py` is the image workdir root.
