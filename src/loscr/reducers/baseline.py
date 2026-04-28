"""Baseline reducer for contamination and baseline-debt summaries."""

from __future__ import annotations

from collections.abc import Sequence

from loscr.hashing import canonical_hash
from loscr.models import BaselineReducerOutput, BaselineRegistryEntry


def baseline_reducer(
    entries: Sequence[BaselineRegistryEntry | dict[str, object]],
) -> BaselineReducerOutput:
    """Return deterministic baseline health data for current MVP checks."""
    parsed = [
        item if isinstance(item, BaselineRegistryEntry) else BaselineRegistryEntry.model_validate(item)
        for item in entries
    ]
    output = BaselineReducerOutput(
        entries={entry.baseline_id: entry for entry in sorted(parsed, key=lambda item: item.baseline_id)},
        contaminated=sorted(entry.baseline_id for entry in parsed if entry.contaminated),
        baseline_debt_by_id={
            entry.baseline_id: entry.baseline_debt
            for entry in sorted(parsed, key=lambda item: item.baseline_id)
            if entry.baseline_debt > 0
        },
        total_baseline_debt=sum(entry.baseline_debt for entry in parsed),
    )
    return output.model_copy(update={"output_hash": canonical_hash(output)})
