from __future__ import annotations

from loscr.hashing import attach_integrity_hash
from loscr.models import ServiceLedgerEvent, ServiceLoadContract, ServiceObligation
from loscr.reducers.service import service_reducer


def _obligation(required: float, reserved: float) -> ServiceObligation:
    return ServiceObligation.model_validate(
        attach_integrity_hash(
            {
                "obligation_id": "obl",
                "created_by_event_id": "evt",
                "claim_id": "claim",
                "channel": "validation",
                "service_unit_id": "ci",
                "deadline_class": "normal",
                "required_quantity": required,
                "reserved_quantity": reserved,
                "completed_quantity": 0.0,
                "cancelled_quantity": 0.0,
                "expired_quantity": 0.0,
                "held_quantity": 0.0,
                "created_at": "2026-01-01T00:00:00Z",
                "due_at": "2026-01-02T00:00:00Z",
                "queue_discipline": "earliest_deadline_first",
                "priority_class": "normal",
                "status": "reserved",
            }
        )
    )


def test_service_reducer_detects_overload() -> None:
    contract = ServiceLoadContract.model_validate(
        attach_integrity_hash(
            {
                "action_type": "edit",
                "substrate_scope": "scope",
                "service_unit_id": "ci",
                "channel": "validation",
                "deadline_class": "normal",
                "expected_load": 1.0,
                "upper_load": 1.0,
                "calibration_window": "w1",
                "minimum_observations": 1,
                "contract_state": "active",
                "last_update_time": "2026-01-01T00:00:00Z",
                "violation_count": 0,
                "calibration_error": 0.0,
                "default_upper_bound": 1.0,
                "reservation_rule": "reserve_upper_load",
                "max_supported_claim_level": "service_controlled",
            }
        )
    )
    service_event = ServiceLedgerEvent.model_validate(
        attach_integrity_hash(
            {
                "service_event_id": "svc",
                "channel": "validation",
                "service_unit_id": "ci",
                "window_id": "2026-01-01",
                "unit": "test",
                "deadline_class": "normal",
                "attempted": 2.0,
                "completed_accepted": 0.0,
            }
        )
    )
    output = service_reducer([service_event], [_obligation(2.0, 1.0)], [contract])
    assert output.overloaded_queues
    assert output.suspect_contracts


def test_service_reducer_reports_oldest_queue_age() -> None:
    output = service_reducer(
        [],
        [_obligation(2.0, 1.0)],
        [],
        control_time="2026-01-01T00:01:00Z",
    )
    assert output.queue_states[0].oldest_age == 60.0


def test_service_reducer_marks_missing_load_contract() -> None:
    output = service_reducer([], [_obligation(1.0, 1.0)], [])
    assert output.missing_contracts == ["validation|ci|normal"]
