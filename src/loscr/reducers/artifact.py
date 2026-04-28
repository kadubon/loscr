"""Ordinary artifact-health reducer."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pydantic import ValidationError

from loscr.hashing import canonical_hash
from loscr.models import ArtifactReducerOutput, EdgeEventEnvelope


def artifact_reducer(
    edge_events: Sequence[dict[str, Any] | EdgeEventEnvelope],
) -> ArtifactReducerOutput:
    """Summarize ordinary artifacts visible in Layer 0 telemetry."""
    counts: dict[str, int] = {}
    dependency_flagged: set[str] = set()
    for raw in edge_events:
        try:
            event = raw if isinstance(raw, EdgeEventEnvelope) else EdgeEventEnvelope.model_validate(raw)
        except ValidationError:
            continue
        counts[event.claim_scope_id] = counts.get(event.claim_scope_id, 0) + 1
        if event.dependency_flag:
            dependency_flagged.add(event.item_id)
    output = ArtifactReducerOutput(
        artifact_count_by_scope=dict(sorted(counts.items())),
        dependency_flagged_artifacts=sorted(dependency_flagged),
    )
    return output.model_copy(update={"output_hash": canonical_hash(output)})
