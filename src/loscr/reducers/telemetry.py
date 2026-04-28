"""Layer 0 edge telemetry reducer."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from pydantic import ValidationError

from loscr.enums import FailureFamily, FieldStatus
from loscr.hashing import canonical_hash, verify_integrity_hash
from loscr.models import EdgeEventEnvelope, ReducerIssue, TelemetryReducerOutput
from loscr.profiles import IDENTIFIER_EVENT_FIELDS, OBSERVABLE_EVENT_FIELDS


def _record_value(record: EdgeEventEnvelope, field: str) -> object:
    if field == "resource_raw":
        return record.resource_raw
    return getattr(record, field)


def telemetry_reducer(
    edge_events: Sequence[EdgeEventEnvelope | dict[str, object]],
) -> TelemetryReducerOutput:
    """Reduce Layer 0 events into coverage and substrate-drift state."""
    events: list[tuple[int, EdgeEventEnvelope]] = []
    issues: list[ReducerIssue] = []
    for fallback_index, raw in enumerate(edge_events):
        try:
            append_index = fallback_index
            if isinstance(raw, EdgeEventEnvelope):
                event = raw
            else:
                append_index = _append_index(raw, fallback_index)
                event = EdgeEventEnvelope.model_validate(
                    {key: value for key, value in raw.items() if not key.startswith("_")}
                )
            events.append((append_index, event))
        except ValidationError as exc:
            issues.append(
                ReducerIssue(
                    family=FailureFamily.TYPE,
                    code="schema_conflict",
                    message=str(exc),
                )
            )

    events = sorted(events, key=lambda item: (item[1].timestamp, item[0], item[1].event_id))
    seen_event_ids: set[str] = set()
    last_substrate_by_scope: dict[str, str] = {}
    coverage_counts: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    coverage_counts_by_key: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    field_status_by_scope: dict[str, dict[str, FieldStatus]] = defaultdict(dict)
    missing_identifier_events: list[str] = []
    integrity_failures: list[str] = []
    parent_link_failures: list[str] = []
    substrate_drift_scopes: set[str] = set()
    latest_event_time: str | None = None

    for _append_order, event in events:
        latest_event_time = max(latest_event_time or event.timestamp, event.timestamp)
        event_missing_identifier = False
        scope = event.claim_scope_id
        station_key = f"{scope}|{event.station_id}|{event.event_type}"
        for field in OBSERVABLE_EVENT_FIELDS:
            value = _record_value(event, field)
            missing = value is None or value == ""
            if field == "parent_event_id" and value is None:
                missing = False
            status = FieldStatus.MISSING if missing else FieldStatus.OBSERVED
            field_status_by_scope[scope][field] = status
            coverage_counts[scope][1] += 1
            coverage_counts_by_key[station_key][1] += 1
            if status in {FieldStatus.OBSERVED, FieldStatus.NOT_APPLICABLE}:
                coverage_counts[scope][0] += 1
                coverage_counts_by_key[station_key][0] += 1
            if field in IDENTIFIER_EVENT_FIELDS and missing:
                event_missing_identifier = True
                issues.append(
                    ReducerIssue(
                        family=FailureFamily.MISSING,
                        code="missing_identifier",
                        message=f"missing identifier field {field}",
                        event_id=event.event_id or None,
                        field=field,
                    )
                )

        if event_missing_identifier:
            missing_identifier_events.append(event.event_id or "<missing_event_id>")
        if not verify_integrity_hash(event):
            integrity_failures.append(event.event_id)
            issues.append(
                ReducerIssue(
                    family=FailureFamily.INTEGRITY,
                    code="integrity_failure",
                    message="edge event integrity hash mismatch",
                    event_id=event.event_id,
                )
            )
        if event.parent_event_id and event.parent_event_id not in seen_event_ids:
            parent_link_failures.append(event.event_id)
            issues.append(
                ReducerIssue(
                    family=FailureFamily.LEDGER,
                    code="parent_link_missing",
                    message="parent event not present in ledger prefix",
                    event_id=event.event_id,
                )
            )
        previous_substrate = last_substrate_by_scope.get(scope)
        if (
            previous_substrate is not None
            and previous_substrate != event.substrate_fingerprint
            and event.event_type != "epoch_bridge"
        ):
            substrate_drift_scopes.add(scope)
        last_substrate_by_scope[scope] = event.substrate_fingerprint
        seen_event_ids.add(event.event_id)

    coverage_by_scope = {
        scope: observed / total if total else 0.0
        for scope, (observed, total) in sorted(coverage_counts.items())
    }
    coverage_by_key = {
        key: observed / total if total else 0.0
        for key, (observed, total) in sorted(coverage_counts_by_key.items())
    }
    output = TelemetryReducerOutput(
        event_count=len(events),
        coverage_by_scope=coverage_by_scope,
        coverage_by_scope_station_stratum=coverage_by_key,
        field_status_by_scope={key: dict(value) for key, value in sorted(field_status_by_scope.items())},
        missing_identifier_events=sorted(set(missing_identifier_events)),
        integrity_failures=sorted(set(integrity_failures)),
        parent_link_failures=sorted(set(parent_link_failures)),
        substrate_drift_scopes=sorted(substrate_drift_scopes),
        latest_event_time=latest_event_time,
        issues=issues,
    )
    return output.model_copy(update={"output_hash": canonical_hash(output)})


def _append_index(raw: dict[str, object], fallback: int) -> int:
    value = raw.get("_append_index", fallback)
    return value if isinstance(value, int) else fallback
