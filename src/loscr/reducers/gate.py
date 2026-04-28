"""Gate reducer for lightweight hard-stop, quarantine, rollback, and warning state."""

from __future__ import annotations

from collections.abc import Sequence

from loscr.enums import GateState
from loscr.hashing import canonical_hash
from loscr.models import GateLedgerEvent, GateReducerOutput, IncidentNode


def gate_reducer(
    gate_events: Sequence[GateLedgerEvent | dict[str, object]],
    incidents: Sequence[IncidentNode | dict[str, object]],
) -> GateReducerOutput:
    """Reduce gate events and incidents into current gate state.

    Gate state is intentionally simple for daily operation. The newest event for
    a target wins, ordered by timestamp then identifier; unresolved incidents
    inject hard-stop state for their incident nodes.
    """
    parsed_events = [
        item if isinstance(item, GateLedgerEvent) else GateLedgerEvent.model_validate(item)
        for item in gate_events
    ]
    parsed_incidents = [
        item if isinstance(item, IncidentNode) else IncidentNode.model_validate(item)
        for item in incidents
    ]
    active: dict[str, GateState] = {}
    claim_by_target: dict[str, str] = {}
    incident_ids: set[str] = set()

    for event in sorted(parsed_events, key=lambda item: (item.timestamp, item.gate_event_id)):
        active[event.target_id] = event.gate_state
        if event.claim_id:
            claim_by_target[event.target_id] = event.claim_id
        if event.incident_id:
            incident_ids.add(event.incident_id)

    for incident in sorted(parsed_incidents, key=lambda item: (item.opened_at, item.incident_id)):
        if incident.resolved_at is None:
            active[incident.node_id] = incident.gate_state
            incident_ids.add(incident.incident_id)

    hard_stop_targets = sorted(
        target for target, state in active.items() if state == GateState.HARD_STOP
    )
    quarantined_targets = sorted(
        target for target, state in active.items() if state == GateState.QUARANTINE
    )
    rollback_targets = sorted(
        target for target, state in active.items() if state == GateState.ROLLBACK
    )
    warned_targets = sorted(target for target, state in active.items() if state == GateState.WARN)
    hard_stop_claim_ids = sorted(
        {
            claim_by_target[target]
            for target in hard_stop_targets
            if target in claim_by_target
        }
    )
    output = GateReducerOutput(
        active_gate_states=dict(sorted(active.items())),
        hard_stop_targets=hard_stop_targets,
        hard_stop_claim_ids=hard_stop_claim_ids,
        quarantined_targets=quarantined_targets,
        rollback_targets=rollback_targets,
        warned_targets=warned_targets,
        incident_ids=sorted(incident_ids),
    )
    return output.model_copy(update={"output_hash": canonical_hash(output)})
