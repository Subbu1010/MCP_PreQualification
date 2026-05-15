# MCP references: (image build — runs all MCP tools via Uvicorn)
# Purpose: Production-style container for the FastAPI + MCP Streamable HTTP server.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN useradd -m -u 1001 appuser

COPY pyproject.toml README.md /app/
COPY src /app/src

RUN pip install --upgrade pip && pip install /app

USER appuser

EXPOSE 8080

CMD ["uvicorn", "mortgage_mcp.main:app", "--host", "0.0.0.0", "--port", "8080"]
