"""
MCP references: (none — convenience entrypoint for operators)
Purpose: Allows `python -m mortgage_mcp.run` as an alternative to `uvicorn mortgage_mcp.main:app`.
"""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(
        "mortgage_mcp.main:app",
        host=host,
        port=port,
        factory=False,
        reload=os.environ.get("UVICORN_RELOAD", "").lower() in {"1", "true", "yes"},
    )


if __name__ == "__main__":
    main()
