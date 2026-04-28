"""Control-state reducer composition helpers."""

from __future__ import annotations

from loscr.hashing import canonical_hash
from loscr.models import ReducerSnapshot
from loscr.reducers.registry import default_reducer_registry


def finalize_snapshot(snapshot: ReducerSnapshot) -> ReducerSnapshot:
    """Attach reducer registry and state hashes to a reducer snapshot."""
    registry_hash = default_reducer_registry().registry_hash()
    with_registry = snapshot.model_copy(update={"reducer_registry_hash": registry_hash})
    return with_registry.model_copy(update={"state_hash": canonical_hash(with_registry)})
