"""Resource-vector reducer."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pydantic import ValidationError

from loscr.hashing import canonical_hash
from loscr.models import EdgeEventEnvelope, ResourceLedgerEvent, ResourceReducerOutput


def resource_reducer(
    edge_events: Sequence[dict[str, Any] | EdgeEventEnvelope],
    resource_events: Sequence[ResourceLedgerEvent | dict[str, object]] | None = None,
) -> ResourceReducerOutput:
    """Aggregate resource-vector accounting from Layer 0 and optional resource ledgers."""
    totals: dict[str, float] = {}
    burden: dict[str, float] = {}
    uncharged_scopes: set[str] = set()

    for raw in edge_events:
        try:
            event = raw if isinstance(raw, EdgeEventEnvelope) else EdgeEventEnvelope.model_validate(raw)
        except ValidationError:
            continue
        _add(totals, f"{event.claim_scope_id}|wall_time", event.resource_raw.wall_time)
        _add(totals, f"{event.claim_scope_id}|compute_seconds", event.resource_raw.compute_seconds)
        _add(totals, f"{event.claim_scope_id}|token_count", float(event.resource_raw.token_count))
        _add(
            totals,
            f"{event.claim_scope_id}|tool_call_count",
            float(event.resource_raw.tool_call_count),
        )

    for item in resource_events or []:
        resource_event = (
            item if isinstance(item, ResourceLedgerEvent) else ResourceLedgerEvent.model_validate(item)
        )
        key = (
            f"{resource_event.claim_scope_id}|{resource_event.resource_class}|{resource_event.unit}"
        )
        _add(totals, key, resource_event.amount)
        if resource_event.charge_kind == "instrumentation_burden":
            _add(burden, resource_event.claim_scope_id, resource_event.amount)
            if not resource_event.charged:
                uncharged_scopes.add(resource_event.claim_scope_id)

    output = ResourceReducerOutput(
        totals_by_scope_resource=dict(sorted(totals.items())),
        instrumentation_burden_by_scope=dict(sorted(burden.items())),
        uncharged_burden_scopes=sorted(uncharged_scopes),
    )
    return output.model_copy(update={"output_hash": canonical_hash(output)})


def _add(target: dict[str, float], key: str, value: float) -> None:
    target[key] = target.get(key, 0.0) + value
