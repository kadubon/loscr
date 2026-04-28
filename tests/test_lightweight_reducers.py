from __future__ import annotations

from loscr.hashing import attach_integrity_hash
from loscr.models import (
    DelayedLabelRecord,
    ExplorationBudgetEvent,
    GateLedgerEvent,
    IncidentNode,
    ResourceLedgerEvent,
    ServiceQueueState,
    ServiceReducerOutput,
    WipItemEvent,
    WipReducerOutput,
)
from loscr.reducers.delayed_label import delayed_label_reducer
from loscr.reducers.exploration import exploration_reducer
from loscr.reducers.gate import gate_reducer
from loscr.reducers.pressure import pressure_reducer
from loscr.reducers.resource import resource_reducer
from loscr.reducers.wip import wip_reducer


def test_gate_reducer_tracks_hard_stop_claim() -> None:
    event = GateLedgerEvent.model_validate(
        attach_integrity_hash(
            {
                "gate_event_id": "gate-1",
                "target_id": "claim",
                "target_type": "claim",
                "claim_id": "claim",
                "claim_scope_id": "scope",
                "gate_state": "hard_stop",
                "reason": "security",
                "timestamp": "2026-01-01T00:00:00Z",
            }
        )
    )
    output = gate_reducer([event], [])
    assert output.hard_stop_claim_ids == ["claim"]


def test_wip_reducer_counts_unresolved_and_terminal_items() -> None:
    active = WipItemEvent.model_validate(
        attach_integrity_hash(
            {
                "item_event_id": "wip-1",
                "item_id": "item-1",
                "claim_scope_id": "scope",
                "station_id": "dev",
                "stratum": "work",
                "item_state": "active",
                "timestamp": "2026-01-01T00:00:00Z",
                "queue_age_raw": 42.0,
            }
        )
    )
    certified = WipItemEvent.model_validate(
        attach_integrity_hash(
            {
                "item_event_id": "wip-2",
                "item_id": "item-2",
                "claim_scope_id": "scope",
                "station_id": "dev",
                "stratum": "work",
                "item_state": "certified",
                "timestamp": "2026-01-01T00:00:00Z",
            }
        )
    )
    output = wip_reducer([active, certified])
    assert output.unresolved_wip_by_scope == {"scope": 1}
    assert output.max_queue_age_by_scope == {"scope": 42.0}
    assert output.certified_items == ["item-2"]


def test_exploration_reducer_tracks_budget_and_incident_freeze() -> None:
    allocate = ExplorationBudgetEvent.model_validate(
        attach_integrity_hash(
            {
                "budget_event_id": "budget-1",
                "claim_id": "claim",
                "event_type": "allocate",
                "resource_class": "generic",
                "amount": 10.0,
                "timestamp": "2026-01-01T00:00:00Z",
            }
        )
    )
    charge = ExplorationBudgetEvent.model_validate(
        attach_integrity_hash(
            {
                "budget_event_id": "budget-2",
                "claim_id": "claim",
                "event_type": "charge",
                "resource_class": "generic",
                "amount": 3.0,
                "timestamp": "2026-01-01T00:01:00Z",
            }
        )
    )
    incident = IncidentNode(
        incident_id="inc-1",
        node_id="node-1",
        incident_type="hard_stop",
        affected_scope="scope",
        opened_at="2026-01-01T00:02:00Z",
    )
    output = exploration_reducer([allocate, charge], [incident])
    assert output.remaining_budget_by_claim == {"claim": 7.0}
    assert output.charges_by_claim == {"claim": 3.0}
    assert output.frozen_claims == ["scope"]


def test_resource_reducer_tracks_uncharged_instrumentation_burden() -> None:
    event = ResourceLedgerEvent.model_validate(
        attach_integrity_hash(
            {
                "resource_event_id": "res-1",
                "timestamp": "2026-01-01T00:00:00Z",
                "claim_scope_id": "scope",
                "resource_class": "audit",
                "unit": "hours",
                "amount": 2.0,
                "charge_kind": "instrumentation_burden",
                "charged": False,
            }
        )
    )
    output = resource_reducer([], [event])
    assert output.instrumentation_burden_by_scope == {"scope": 2.0}
    assert output.uncharged_burden_scopes == ["scope"]


def test_delayed_label_reducer_marks_missing_assignment_probability() -> None:
    label = DelayedLabelRecord.model_validate(
        attach_integrity_hash(
            {
                "label_id": "label-1",
                "item_id": "item-1",
                "claim_id": "claim",
                "stratum": "work",
                "evaluator_id": "eval",
                "assignment_time": "2026-01-01T00:00:00Z",
            }
        )
    )
    output = delayed_label_reducer([label])
    assert output.label_count_by_claim == {"claim": 1}
    assert output.missing_assignment_probability_labels == ["label-1"]


def test_delayed_label_reducer_marks_invalid_assignment_probability() -> None:
    label = DelayedLabelRecord.model_validate(
        attach_integrity_hash(
            {
                "label_id": "label-1",
                "item_id": "item-1",
                "claim_id": "claim",
                "stratum": "work",
                "evaluator_id": "eval",
                "assignment_probability": 1.5,
                "assignment_time": "2026-01-01T00:00:00Z",
            }
        )
    )
    output = delayed_label_reducer([label])
    assert output.missing_assignment_probability_labels == ["label-1"]


def test_pressure_reducer_combines_wip_and_service_queue_pressure() -> None:
    wip = WipReducerOutput(unresolved_wip_by_scope_station_stratum={"scope|dev|work": 2})
    service = ServiceReducerOutput(
        queue_states=[
            ServiceQueueState(
                channel="validation",
                service_unit_id="ci",
                deadline_class="normal",
                window_id="w1",
                outstanding=3.0,
                oldest_age=4.0,
                overloaded=True,
            )
        ]
    )
    output = pressure_reducer(wip, service)
    assert output.pressure_by_station["dev"] == 2.0
    assert output.pressure_by_station["ci"] == 8.0
