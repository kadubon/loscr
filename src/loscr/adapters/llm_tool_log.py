"""Adapter for local LLM/tool-call JSONL logs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loscr.adapters.jsonl import read_jsonl_records
from loscr.hashing import attach_integrity_hash, canonical_hash
from loscr.models import EdgeEventEnvelope, ResourceRaw


def llm_tool_log_to_edge_events(
    path: str | Path,
    *,
    claim_scope_id: str = "default",
    station_id: str = "llm_tool",
    policy_id: str = "local-log",
) -> list[EdgeEventEnvelope]:
    """Convert generic local LLM/tool-call logs into Layer 0 events."""
    events: list[EdgeEventEnvelope] = []
    for index, row in enumerate(read_jsonl_records(path)):
        prompt_hash = row.get("prompt_hash") or canonical_hash(row.get("prompt", ""))
        output_hash = row.get("output_hash") or canonical_hash(row.get("output", ""))
        tool_manifest_hash = row.get("tool_manifest_hash") or canonical_hash(
            row.get("tools", row.get("tool", "none"))
        )
        event_id = str(row.get("event_id") or f"llm:{canonical_hash({'path': Path(path).name, 'i': index})}")
        data: dict[str, Any] = {
            "event_id": event_id,
            "event_type": str(row.get("event_type", "llm_tool_call")),
            "timestamp": str(row.get("timestamp", "1970-01-01T00:00:00Z")),
            "item_id": str(row.get("item_id", event_id)),
            "parent_event_id": row.get("parent_event_id"),
            "station_id": str(row.get("station_id", station_id)),
            "policy_id": str(row.get("policy_id", policy_id)),
            "action_type": str(row.get("action_type", "tool_call")),
            "substrate_fingerprint": canonical_hash(
                {
                    "model": row.get("model", "unknown"),
                    "tool_manifest_hash": tool_manifest_hash,
                }
            ),
            "status_raw": str(row.get("status_raw", row.get("status", "unknown"))),
            "resource_raw": ResourceRaw(
                wall_time=float(row.get("wall_time", 0.0) or 0.0),
                compute_seconds=float(row.get("compute_seconds", 0.0) or 0.0),
                token_count=int(row.get("token_count", 0) or 0),
                tool_call_count=int(row.get("tool_call_count", 1) or 1),
            ).model_dump(mode="json"),
            "queue_channel": str(row.get("queue_channel", "llm_tool")),
            "queue_age_raw": float(row.get("queue_age_raw", 0.0) or 0.0),
            "dependency_flag": bool(row.get("dependency_flag", False)),
            "reuse_count": int(row.get("reuse_count", 0) or 0),
            "input_hash": str(prompt_hash),
            "output_hash": str(output_hash),
            "claim_scope_id": str(row.get("claim_scope_id", claim_scope_id)),
        }
        events.append(EdgeEventEnvelope.model_validate(attach_integrity_hash(data)))
    return events
