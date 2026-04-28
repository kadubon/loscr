"""Work-in-process reducer for lightweight daily operation."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from loscr.enums import ItemState
from loscr.hashing import canonical_hash
from loscr.models import WipItemEvent, WipReducerOutput


TERMINAL_STATES = {
    ItemState.CERTIFIED,
    ItemState.REJECTED,
    ItemState.EXPIRED,
    ItemState.QUARANTINED,
}


def wip_reducer(item_events: Sequence[WipItemEvent | dict[str, object]]) -> WipReducerOutput:
    """Compute unresolved WIP, queue age, and terminal item lists."""
    parsed = [
        item if isinstance(item, WipItemEvent) else WipItemEvent.model_validate(item)
        for item in item_events
    ]
    latest_by_item: dict[str, WipItemEvent] = {}
    for event in sorted(parsed, key=lambda item: (item.timestamp, item.item_event_id)):
        latest_by_item[event.item_id] = event

    unresolved_by_scope: dict[str, int] = defaultdict(int)
    unresolved_by_key: dict[str, int] = defaultdict(int)
    max_age_by_scope: dict[str, float] = defaultdict(float)
    certified: list[str] = []
    rejected: list[str] = []
    expired: list[str] = []
    quarantined: list[str] = []

    for item_id, event in sorted(latest_by_item.items()):
        if event.item_state not in TERMINAL_STATES:
            unresolved_by_scope[event.claim_scope_id] += 1
            key = f"{event.claim_scope_id}|{event.station_id}|{event.stratum}"
            unresolved_by_key[key] += 1
            max_age_by_scope[event.claim_scope_id] = max(
                max_age_by_scope[event.claim_scope_id], event.queue_age_raw
            )
        elif event.item_state == ItemState.CERTIFIED:
            certified.append(item_id)
        elif event.item_state == ItemState.REJECTED:
            rejected.append(item_id)
        elif event.item_state == ItemState.EXPIRED:
            expired.append(item_id)
        elif event.item_state == ItemState.QUARANTINED:
            quarantined.append(item_id)

    output = WipReducerOutput(
        unresolved_wip_by_scope=dict(sorted(unresolved_by_scope.items())),
        unresolved_wip_by_scope_station_stratum=dict(sorted(unresolved_by_key.items())),
        max_queue_age_by_scope=dict(sorted(max_age_by_scope.items())),
        certified_items=sorted(certified),
        rejected_items=sorted(rejected),
        expired_items=sorted(expired),
        quarantined_items=sorted(quarantined),
    )
    return output.model_copy(update={"output_hash": canonical_hash(output)})
