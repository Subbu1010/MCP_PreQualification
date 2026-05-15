"""
MCP references: explain_eligibility_decision
Purpose: Google Gemini access (REST) with a deterministic mock fallback — swap auth here without touching services.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Final

import httpx

from mortgage_mcp.common.settings import get_settings

logger = logging.getLogger(__name__)

_GENERATE_URL: Final[str] = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


def _mock_response(user_payload: str) -> tuple[str, str]:
    """Deterministic narrative when API keys are not configured (local dev / CI)."""
    try:
        payload = json.loads(user_payload)
    except json.JSONDecodeError:
        payload = {}
    eligible = payload.get("eligible")
    status = payload.get("status", "UNKNOWN")
    dti = payload.get("dti_ratio")
    ltv = payload.get("ltv_ratio")
    failed = payload.get("failed_rules") or []
    drivers = []
    for fr in failed:
        if isinstance(fr, dict) and fr.get("severity") == "FAIL":
            drivers.append(fr.get("rule_id", "RULE"))
    narrative = (
        f"Mock underwriting explanation (no live LLM): status={status}, eligible={eligible}. "
        f"Key metrics include DTI {dti}% and LTV {ltv}%. "
        f"Primary hard-stop drivers (if any): {', '.join(drivers) or 'none listed'}. "
        "This is not a credit decision and does not replace licensed loan officer review."
    )
    structured = {
        "primary_decline_drivers": drivers or (["NONE"] if eligible else ["UNKNOWN"]),
        "mitigations_to_consider": [
            "Reduce financed amount to improve LTV",
            "Pay down revolving debt to improve DTI",
            "Verify reserves and document compensating factors",
        ],
    }
    raw = json.dumps({"narrative": narrative, "structured_summary": structured})
    return raw, "mock:offline-template"


async def generate_json_text(*, system: str, user: str) -> tuple[str, str]:
    """
    Calls Gemini when `GOOGLE_API_KEY` is set; otherwise returns `_mock_response(user)`.

    NOTE: Organizations using Vertex AI with custom auth can replace this module's internals while
    keeping `LLMProvider` call sites stable in `service.py`.
    """
    settings = get_settings()
    if not settings.google_api_key:
        logger.info("LLM provider: using offline mock (GOOGLE_API_KEY not set)")
        return _mock_response(user)

    url = _GENERATE_URL.format(model=settings.gemini_model)
    params = {"key": settings.google_api_key}
    body: dict[str, Any] = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, params=params, json=body)
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            mid = f"google:{settings.gemini_model}"
            return text, mid
    except Exception as exc:  # noqa: BLE001
        logger.warning("Gemini REST call failed; falling back to mock output: %s", exc)
        return _mock_response(user)


def extract_json_object(text: str) -> dict[str, Any]:
    """Parses JSON object from model output; tolerates minor fences if present."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned)
