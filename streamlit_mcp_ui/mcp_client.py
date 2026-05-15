"""
MCP references: calculate_dti, calculate_ltv, check_borrower_eligibility, recommend_loan_products,
                 search_mortgage_policy, explain_eligibility_decision (via tools/call)
Purpose: Async MCP Streamable HTTP client used by every Streamlit page to invoke the remote server.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.types import CallToolResult, TextContent


def get_mcp_server_url() -> str:
    """Base URL for MCP Streamable HTTP (must include `/mcp` path as deployed on the API server)."""
    return os.environ.get("MCP_SERVER_URL", "http://127.0.0.1:8080/mcp").rstrip("/")


def _parse_tool_result(result: CallToolResult) -> dict[str, Any]:
    if result.isError:
        msg_parts: list[str] = []
        for block in result.content:
            if isinstance(block, TextContent):
                msg_parts.append(block.text)
            elif isinstance(block, dict) and block.get("type") == "text":
                msg_parts.append(str(block.get("text", "")))
        raise RuntimeError(msg_parts[0] if msg_parts else "MCP tool returned isError=true with no message")

    if result.structuredContent is not None:
        return dict(result.structuredContent)

    for block in result.content:
        if isinstance(block, TextContent):
            try:
                parsed = json.loads(block.text)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                return {"_text": block.text}
        if isinstance(block, dict) and block.get("type") == "text":
            try:
                parsed = json.loads(str(block["text"]))
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                return {"_text": block.get("text")}

    return {"_raw": [type(b).__name__ for b in result.content]}


async def call_mcp_tool_async(tool_name: str, arguments: dict[str, Any] | None) -> dict[str, Any]:
    url = get_mcp_server_url()
    async with streamable_http_client(url) as (read_stream, write_stream, _get_session_id):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments or {})
            return _parse_tool_result(result)


def call_mcp_tool(tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    """Synchronous entry for Streamlit button handlers (fresh asyncio loop per call)."""
    return asyncio.run(call_mcp_tool_async(tool_name, arguments))


async def list_tools_async() -> list[str]:
    url = get_mcp_server_url()
    async with streamable_http_client(url) as (read_stream, write_stream, _get_session_id):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            return [t.name for t in tools.tools]


def list_tools_sync() -> list[str]:
    return asyncio.run(list_tools_async())
