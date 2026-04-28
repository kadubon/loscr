from __future__ import annotations

from loscr.reducers.telemetry import telemetry_reducer


def test_telemetry_reducer_is_deterministic(make_event) -> None:  # type: ignore[no-untyped-def]
    events = [make_event(event_id="evt-2"), make_event(event_id="evt-1")]
    left = telemetry_reducer(events)
    right = telemetry_reducer(list(reversed(events)))
    assert left.output_hash == right.output_hash
    assert left.coverage_by_scope["scope"] == 1.0


def test_telemetry_reducer_uses_append_order_before_identifier(make_event) -> None:  # type: ignore[no-untyped-def]
    parent = make_event(event_id="z-parent").model_dump(mode="json")
    parent["_append_index"] = 0
    child = make_event(event_id="a-child", parent_event_id="z-parent").model_dump(mode="json")
    child["_append_index"] = 1
    output = telemetry_reducer([child, parent])
    assert output.parent_link_failures == []
