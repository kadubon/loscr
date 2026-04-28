"""Layer 1 service-control reducer."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime, timezone

from loscr.enums import ServiceContractState
from loscr.hashing import canonical_hash, verify_integrity_hash
from loscr.models import (
    ServiceLedgerEvent,
    ServiceLoadContract,
    ServiceObligation,
    ServiceQueueState,
    ServiceReducerOutput,
)


def _queue_key(channel: str, service_unit_id: str, deadline_class: str, window_id: str) -> str:
    return f"{channel}|{service_unit_id}|{deadline_class}|{window_id}"


def service_reducer(
    service_events: Sequence[ServiceLedgerEvent | dict[str, object]],
    obligations: Sequence[ServiceObligation | dict[str, object]],
    contracts: Sequence[ServiceLoadContract | dict[str, object]],
    *,
    control_time: str | None = None,
) -> ServiceReducerOutput:
    """Reduce service ledgers into queues and service-contract health."""
    parsed_events = [
        item if isinstance(item, ServiceLedgerEvent) else ServiceLedgerEvent.model_validate(item)
        for item in service_events
    ]
    parsed_obligations = [
        item if isinstance(item, ServiceObligation) else ServiceObligation.model_validate(item)
        for item in obligations
    ]
    parsed_contracts = [
        item if isinstance(item, ServiceLoadContract) else ServiceLoadContract.model_validate(item)
        for item in contracts
    ]
    parsed_events.sort(key=lambda item: (item.window_id, item.service_event_id))
    parsed_obligations.sort(key=lambda item: (item.created_at, item.obligation_id))
    parsed_contracts.sort(key=lambda item: (item.channel, item.action_type, item.service_unit_id))

    queue_totals: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    violation_counts: dict[str, int] = {}
    contract_states: dict[str, ServiceContractState] = {}
    contract_by_key: dict[tuple[str, str, str], ServiceLoadContract] = {}
    missing_contracts: set[str] = set()
    integrity_failures: set[str] = set()

    for contract in parsed_contracts:
        contract_lookup_key = (contract.channel, contract.service_unit_id, contract.deadline_class)
        contract_by_key[contract_lookup_key] = contract
        contract_id = _queue_key(
            contract.channel,
            contract.service_unit_id,
            contract.deadline_class,
            contract.action_type,
        )
        if not verify_integrity_hash(contract):
            integrity_failures.add(contract_id)
        state = contract.contract_state
        if contract.minimum_observations > 0 and contract.contract_state == ServiceContractState.DRAFT:
            state = ServiceContractState.DRAFT
        if contract.violation_count > 0 and state == ServiceContractState.ACTIVE:
            state = ServiceContractState.SUSPECT
        if contract.violation_count > 1:
            state = ServiceContractState.QUARANTINED
        violation_counts[contract_id] = contract.violation_count
        contract_states[contract_id] = state

    for obligation in parsed_obligations:
        queue_key = _queue_key(
            obligation.channel,
            obligation.service_unit_id,
            obligation.deadline_class,
            obligation.created_at[:10],
        )
        totals = queue_totals[queue_key]
        totals["required"] += obligation.required_quantity
        totals["reserved"] += obligation.reserved_quantity
        totals["completed"] += obligation.completed_quantity
        totals["cancelled"] += obligation.cancelled_quantity
        totals["expired"] += obligation.expired_quantity
        totals["held"] += obligation.held_quantity
        if not verify_integrity_hash(obligation):
            integrity_failures.add(obligation.obligation_id)
        if (obligation.channel, obligation.service_unit_id, obligation.deadline_class) not in contract_by_key:
            missing_contracts.add(
                f"{obligation.channel}|{obligation.service_unit_id}|{obligation.deadline_class}"
            )
        if (
            obligation.reserved_quantity < obligation.required_quantity
            or obligation.expired_quantity > 0
            or obligation.held_quantity > 0
        ):
            totals["overload_signal"] += 1
        if obligation.required_quantity > obligation.completed_quantity:
            totals["oldest_age"] = max(
                totals["oldest_age"], _age_seconds(obligation.created_at, control_time)
            )

    for event in parsed_events:
        queue_key = _queue_key(
            event.channel, event.service_unit_id, event.deadline_class, event.window_id
        )
        totals = queue_totals[queue_key]
        totals["completed"] += event.completed_accepted
        totals["cancelled"] += event.cancelled
        totals["expired"] += event.expired
        totals["held"] += event.held
        if not verify_integrity_hash(event):
            integrity_failures.add(event.service_event_id)
            totals["overload_signal"] += 1
        matched_contract = contract_by_key.get(
            (event.channel, event.service_unit_id, event.deadline_class)
        )
        if matched_contract is None:
            missing_contracts.add(f"{event.channel}|{event.service_unit_id}|{event.deadline_class}")
        if (
            matched_contract is not None
            and matched_contract.upper_load > 0
            and event.attempted > matched_contract.upper_load
        ):
            contract_id = _queue_key(
                matched_contract.channel,
                matched_contract.service_unit_id,
                matched_contract.deadline_class,
                matched_contract.action_type,
            )
            violation_counts[contract_id] = violation_counts.get(contract_id, 0) + 1
            contract_states[contract_id] = (
                ServiceContractState.QUARANTINED
                if violation_counts[contract_id] > 1
                else ServiceContractState.SUSPECT
            )

    queue_states: list[ServiceQueueState] = []
    overloaded_queues: list[str] = []
    for queue_key, totals in sorted(queue_totals.items()):
        channel, service_unit_id, deadline_class, window_id = queue_key.split("|", maxsplit=3)
        completed_like = totals["completed"] + totals["cancelled"] + totals["expired"]
        outstanding = max(0.0, totals["required"] - completed_like)
        overloaded = bool(totals["overload_signal"]) or outstanding > max(
            totals["reserved"] - totals["completed"], 0.0
        )
        if overloaded:
            overloaded_queues.append(queue_key)
        queue_states.append(
            ServiceQueueState(
                channel=channel,
                service_unit_id=service_unit_id,
                deadline_class=deadline_class,
                window_id=window_id,
                required=totals["required"],
                reserved=totals["reserved"],
                completed=totals["completed"],
                cancelled=totals["cancelled"],
                expired=totals["expired"],
                held=totals["held"],
                outstanding=outstanding,
                oldest_age=totals["oldest_age"],
                overloaded=overloaded,
            )
        )

    output = ServiceReducerOutput(
        queue_states=queue_states,
        contract_states=contract_states,
        violation_counts=violation_counts,
        uncalibrated_contracts=[
            key for key, state in contract_states.items() if state == ServiceContractState.DRAFT
        ],
        suspect_contracts=[
            key for key, state in contract_states.items() if state == ServiceContractState.SUSPECT
        ],
        quarantined_contracts=[
            key for key, state in contract_states.items() if state == ServiceContractState.QUARANTINED
        ],
        missing_contracts=sorted(missing_contracts),
        integrity_failures=sorted(integrity_failures),
        overloaded_queues=sorted(overloaded_queues),
    )
    return output.model_copy(update={"output_hash": canonical_hash(output)})


def _age_seconds(created_at: str, control_time: str | None) -> float:
    if control_time is None:
        return 0.0
    try:
        created = _parse_timestamp(created_at)
        current = _parse_timestamp(control_time)
    except ValueError:
        return 0.0
    return max(0.0, (current - created).total_seconds())


def _parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
