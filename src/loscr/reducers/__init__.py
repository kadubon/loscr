"""Deterministic reducers for append-only LOSCR ledgers."""

from __future__ import annotations

from typing import Any

from loscr.reducers.artifact import artifact_reducer
from loscr.reducers.baseline import baseline_reducer
from loscr.reducers.claim import claim_reducer
from loscr.reducers.delayed_label import delayed_label_reducer
from loscr.reducers.dependency import dependency_reducer
from loscr.reducers.exploration import exploration_reducer
from loscr.reducers.gate import gate_reducer
from loscr.reducers.library import library_reducer
from loscr.reducers.pressure import pressure_reducer
from loscr.reducers.registry import ReducerRegistry, ReducerSpec, default_reducer_registry
from loscr.reducers.resource import resource_reducer
from loscr.reducers.service import service_reducer
from loscr.reducers.telemetry import telemetry_reducer
from loscr.reducers.wip import wip_reducer

__all__ = [
    "baseline_reducer",
    "claim_reducer",
    "artifact_reducer",
    "delayed_label_reducer",
    "dependency_reducer",
    "exploration_reducer",
    "gate_reducer",
    "library_reducer",
    "ordered_records",
    "pressure_reducer",
    "ReducerRegistry",
    "ReducerSpec",
    "resource_reducer",
    "service_reducer",
    "telemetry_reducer",
    "wip_reducer",
    "default_reducer_registry",
]


def ordered_records(records: list[Any], id_field: str) -> list[Any]:
    """Order records by event time, append order, then identifier."""

    def key(record: Any) -> tuple[str, int, str]:
        timestamp = getattr(record, "timestamp", None)
        if timestamp is None:
            timestamp = getattr(record, "created_at", None)
        if timestamp is None:
            timestamp = getattr(record, "opened_at", None)
        if timestamp is None:
            timestamp = getattr(record, "last_update_time", None)
        append_index = getattr(record, "_append_index", 0)
        identifier = getattr(record, id_field, "")
        return (str(timestamp or ""), int(append_index or 0), str(identifier or ""))

    return sorted(records, key=key)
