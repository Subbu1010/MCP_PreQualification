"""
MCP references: search_mortgage_policy
Purpose: Optional offline script to warm-build the policy FAISS index (same logic as app startup).
"""

from __future__ import annotations

import asyncio

from mortgage_mcp.common.logging.structured_logger import configure_logging


async def _main() -> None:
    configure_logging()
    from mortgage_mcp.tools.search_mortgage_policy.bootstrap import init_policy_index

    await init_policy_index()
    print("Policy index built successfully.")


if __name__ == "__main__":
    asyncio.run(_main())
