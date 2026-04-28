"""Layer 2 certified-library reducer."""

from __future__ import annotations

from collections.abc import Sequence

from loscr.enums import LibraryState, TrustedBaseState
from loscr.hashing import canonical_hash, verify_integrity_hash
from loscr.models import (
    LibraryEntry,
    LibraryReducerOutput,
    PromotionAttributionRecord,
    ReinvestmentLedgerEdge,
    ReplayRecord,
    TrustedBaseEntry,
)


def library_reducer(
    replay_records: Sequence[ReplayRecord | dict[str, object]],
    registry: Sequence[TrustedBaseEntry | dict[str, object]],
    lineage: Sequence[PromotionAttributionRecord | ReinvestmentLedgerEdge | dict[str, object]]
    | None = None,
    maintenance: Sequence[LibraryEntry | dict[str, object]] | None = None,
    *,
    control_time: str = "9999-12-31T00:00:00Z",
) -> LibraryReducerOutput:
    """Compute conservative certified-library states."""
    del lineage
    records = [
        item if isinstance(item, ReplayRecord) else ReplayRecord.model_validate(item)
        for item in replay_records
    ]
    trusted_entries = [
        item if isinstance(item, TrustedBaseEntry) else TrustedBaseEntry.model_validate(item)
        for item in registry
    ]
    entries = [
        item if isinstance(item, LibraryEntry) else LibraryEntry.model_validate(item)
        for item in (maintenance or [])
    ]
    trusted_by_id = {entry.trusted_base_id: entry for entry in trusted_entries}
    entry_state: dict[str, LibraryState] = {entry.library_entry_id: entry.state for entry in entries}
    due_entries: set[str] = set()
    quarantined_entries: set[str] = set()
    promoted_entries: set[str] = {
        entry.library_entry_id for entry in entries if entry.state == LibraryState.PROMOTED
    }

    for record in sorted(records, key=lambda item: item.library_entry_id):
        trusted = trusted_by_id.get(record.trusted_base_id)
        state = entry_state.get(record.library_entry_id, LibraryState.CANDIDATE)
        if not verify_integrity_hash(record):
            state = LibraryState.QUARANTINED
        elif trusted is None or trusted.state != TrustedBaseState.ACTIVE:
            state = LibraryState.QUARANTINED
        elif record.maintenance_due_time < control_time and state not in {
            LibraryState.PROMOTED,
            LibraryState.RETIRED,
        }:
            state = LibraryState.DUE
        elif state in {LibraryState.CANDIDATE, LibraryState.EXPERIMENTAL}:
            state = LibraryState.ADMITTED
        entry_state[record.library_entry_id] = state
        if state == LibraryState.QUARANTINED:
            quarantined_entries.add(record.library_entry_id)
        if state == LibraryState.DUE:
            due_entries.add(record.library_entry_id)
        if state == LibraryState.PROMOTED:
            promoted_entries.add(record.library_entry_id)

    output = LibraryReducerOutput(
        states_by_entry=dict(sorted(entry_state.items())),
        quarantined_entries=sorted(quarantined_entries),
        due_entries=sorted(due_entries),
        promoted_entries=sorted(promoted_entries),
    )
    return output.model_copy(update={"output_hash": canonical_hash(output)})
