from __future__ import annotations

import pytest

from loscr.reducers.registry import ReducerRegistry, default_reducer_registry


def test_default_reducer_registry_is_discoverable() -> None:
    registry = default_reducer_registry()
    assert {
        "telemetry",
        "service",
        "claim",
        "dependency",
        "library",
        "resource",
        "delayed_label",
        "pressure",
        "artifact",
    } <= set(registry.list_names())
    assert registry.registry_hash().startswith("sha256:")
    assert registry.get("telemetry").output_model.__name__ == "TelemetryReducerOutput"


def test_reducer_registry_rejects_unknown_names() -> None:
    registry = ReducerRegistry()
    with pytest.raises(KeyError):
        registry.get("missing")
