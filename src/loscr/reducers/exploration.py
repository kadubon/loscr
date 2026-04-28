"""Exploration-budget reducer."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from loscr.hashing import canonical_hash
from loscr.models import ExplorationBudgetEvent, ExplorationReducerOutput, IncidentNode


def exploration_reducer(
    budget_events: Sequence[ExplorationBudgetEvent | dict[str, object]],
    incidents: Sequence[IncidentNode | dict[str, object]],
) -> ExplorationReducerOutput:
    """Reduce exploration budget allocations, charges, releases, and freezes."""
    parsed = [
        item if isinstance(item, ExplorationBudgetEvent) else ExplorationBudgetEvent.model_validate(item)
        for item in budget_events
    ]
    parsed_incidents = [
        item if isinstance(item, IncidentNode) else IncidentNode.model_validate(item)
        for item in incidents
    ]
    remaining: dict[str, float] = defaultdict(float)
    charges: dict[str, float] = defaultdict(float)
    frozen: set[str] = set()

    for event in sorted(parsed, key=lambda item: (item.timestamp, item.budget_event_id)):
        if event.event_type == "allocate":
            remaining[event.claim_id] += event.amount
        elif event.event_type == "charge":
            remaining[event.claim_id] -= event.amount
            charges[event.claim_id] += event.amount
        elif event.event_type == "release":
            remaining[event.claim_id] += event.amount
        elif event.event_type == "freeze":
            frozen.add(event.claim_id)

    for incident in parsed_incidents:
        if incident.resolved_at is None and incident.affected_scope:
            frozen.add(incident.affected_scope)

    output = ExplorationReducerOutput(
        remaining_budget_by_claim=dict(sorted(remaining.items())),
        charges_by_claim=dict(sorted(charges.items())),
        frozen_claims=sorted(frozen),
    )
    return output.model_copy(update={"output_hash": canonical_hash(output)})
