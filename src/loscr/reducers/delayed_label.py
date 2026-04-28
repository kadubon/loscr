"""Delayed-label reducer."""

from __future__ import annotations

from collections.abc import Sequence

from loscr.hashing import canonical_hash
from loscr.models import DelayedLabelRecord, DelayedLabelReducerOutput


def delayed_label_reducer(
    labels: Sequence[DelayedLabelRecord | dict[str, object]],
) -> DelayedLabelReducerOutput:
    """Compute assignment-probability and missingness summaries for delayed labels."""
    count_by_claim: dict[str, int] = {}
    missing_by_claim: dict[str, int] = {}
    missing_assignment: list[str] = []

    for item in labels:
        label = item if isinstance(item, DelayedLabelRecord) else DelayedLabelRecord.model_validate(item)
        count_by_claim[label.claim_id] = count_by_claim.get(label.claim_id, 0) + 1
        if (
            label.assignment_probability is None
            or label.assignment_probability <= 0
            or label.assignment_probability > 1
        ):
            missing_assignment.append(label.label_id)
        if label.missingness_state != "observed":
            missing_by_claim[label.claim_id] = missing_by_claim.get(label.claim_id, 0) + 1

    missingness_by_claim = {
        claim_id: missing_by_claim.get(claim_id, 0) / count
        for claim_id, count in sorted(count_by_claim.items())
        if count > 0
    }
    output = DelayedLabelReducerOutput(
        label_count_by_claim=dict(sorted(count_by_claim.items())),
        missing_assignment_probability_labels=sorted(missing_assignment),
        missingness_by_claim=missingness_by_claim,
    )
    return output.model_copy(update={"output_hash": canonical_hash(output)})
