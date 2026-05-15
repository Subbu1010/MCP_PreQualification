"""
MCP references: explain_eligibility_decision
Purpose: Abstract LLM interface so Vertex/Gemini wiring stays isolated from business narrative assembly.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """Minimal contract implemented by `vertex_gemini_provider.py` for this MCP tool only."""

    async def generate_json_text(self, *, system: str, user: str) -> tuple[str, str]:
        """
        Returns (raw_model_text, model_id_label).

        The implementation should encourage JSON-shaped output; the caller validates/parses defensively.
        """
