"""
MCP references: calculate_dti, calculate_ltv, check_borrower_eligibility, recommend_loan_products,
                 search_mortgage_policy, explain_eligibility_decision
Purpose: Exposes the ASGI `app` used by Uvicorn — mounts Streamable HTTP MCP and lightweight health routes.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from mortgage_mcp.common.logging.structured_logger import configure_logging
from mortgage_mcp.transport.tool_registry import build_mortgage_mcp

_mcp = build_mortgage_mcp()
_mcp_http = _mcp.streamable_http_app()


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    async with _mcp.session_manager.run():
        from mortgage_mcp.tools.search_mortgage_policy.bootstrap import init_policy_index

        await init_policy_index()
        yield


app = FastAPI(title="Mortgage Eligibility MCP", version="0.1.0", lifespan=lifespan)
app.mount("/mcp", _mcp_http)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> dict[str, str]:
    """Readiness includes policy index warmup for `search_mortgage_policy`."""
    from mortgage_mcp.tools.search_mortgage_policy.bootstrap import get_policy_index

    _ = get_policy_index()
    return {"status": "ready"}
