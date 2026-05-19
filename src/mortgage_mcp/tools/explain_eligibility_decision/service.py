"""
MCP references: explain_eligibility_decision
Purpose: Builds prompts and calls the isolated Gemini provider to return governed explanation JSON.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from mortgage_mcp.common.errors.app_errors import LLM_REFUSAL, VALIDATION_ERROR, ToolError
from mortgage_mcp.tools.explain_eligibility_decision.ai_provider import vertex_gemini_provider as gemini
from mortgage_mcp.tools.explain_eligibility_decision.schemas import EligibilitySnapshot

SYSTEM = """You are a mortgage banking assistant generating an advisory explanation for internal staff.
Return STRICT JSON with keys: narrative (string), structured_summary (object with keys primary_decline_drivers array of strings,
mitigations_to_consider array of strings). Do not claim legal authority. Use only facts present in the user JSON."""


async def run_explain_eligibility_decision(raw: dict[str, Any]) -> dict[str, Any]:
    correlation_id = str(uuid.uuid4())
    snap_raw = raw.get("eligibility_snapshot")
    if not isinstance(snap_raw, dict):
        raise ToolError(VALIDATION_ERROR, "eligibility_snapshot must be an object")

    language = str(raw.get("language", "en-US"))
    _ = language  # reserved for future localized prompts

    try:
        snapshot = EligibilitySnapshot.model_validate(snap_raw)
    except Exception as exc:  # noqa: BLE001
        raise ToolError(VALIDATION_ERROR, str(exc)) from exc

    user_json = json.dumps(snapshot.model_dump(), indent=2)
    raw_text, model_id = await gemini.generate_json_text(system=SYSTEM, user=user_json)

    try:
        parsed = gemini.extract_json_object(raw_text)
    except json.JSONDecodeError as exc:
        raise ToolError(LLM_REFUSAL, "Model output was not valid JSON") from exc

    narrative = parsed.get("narrative")
    structured = parsed.get("structured_summary")
    if not narrative or not isinstance(structured, dict):
        raise ToolError(LLM_REFUSAL, "Model JSON missing required keys")

    citations_used = [pr.model_dump() for pr in snapshot.policy_references]

    return {
        "success": True,
        "tool": "mortgage_explain_eligibility_decision",
        "correlation_id": correlation_id,
        "model_id": model_id,
        "narrative": narrative,
        "structured_summary": structured,
        "citations_used": citations_used,
        "disclaimer": (
            "Advisory explanation for internal personnel and AI agents; not a Loan Estimate, "
            "not an underwriting credit decision, and not legal advice."
        ),
    }
