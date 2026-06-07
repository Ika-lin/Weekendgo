"""
Structured response helpers for Weekendgo agent.

The frontend can keep using reply/toolCalls/trip, while newer screens can
consume intent, state, suggestions, and actions directly.
"""
from __future__ import annotations

from typing import Any
import time


def agent_response(
    *,
    reply: str,
    intent: str = "smalltalk",
    stage: str = "done",
    tool_calls: list[dict[str, Any]] | None = None,
    trip: dict[str, Any] | None = None,
    suggestions: list[dict[str, Any]] | None = None,
    actions: list[dict[str, Any]] | None = None,
    needs: list[str] | None = None,
    state_patch: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "reply": reply,
        "intent": intent,
        "stage": stage,
        "tool_calls": tool_calls or [],
        "trip": trip,
        "suggestions": suggestions or [],
        "actions": actions or [],
        "needs": needs or [],
        "state_patch": state_patch or {},
        "metadata": metadata or {},
    }


def public_payload(result: dict[str, Any]) -> dict[str, Any]:
    """Normalize a result before returning it from Flask routes."""
    return {
        "reply": result.get("reply", ""),
        "intent": result.get("intent", "smalltalk"),
        "stage": result.get("stage", "done"),
        "toolCalls": result.get("tool_calls", []),
        "trip": result.get("trip"),
        "suggestions": result.get("suggestions", []),
        "actions": result.get("actions", []),
        "needs": result.get("needs", []),
        "metadata": result.get("metadata", {}),
    }


def safe_json_result(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}

    import json

    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {"value": parsed}
    except json.JSONDecodeError:
        return {"text": raw}


def tool_log(
    tool: str,
    *,
    args: dict[str, Any] | None = None,
    result: dict[str, Any] | None = None,
    status: str = "success",
    source: str = "state_machine",
    error: str | None = None,
) -> dict[str, Any]:
    payload = {
        "tool": tool,
        "source": source,
        "status": status,
        "args": args or {},
        "result": result or {},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
    }
    if error:
        payload["error"] = error
    return payload
