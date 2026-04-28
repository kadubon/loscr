"""Claim-state reducer."""

from __future__ import annotations

from collections.abc import Sequence

from loscr.enums import CheckerStatus, ClaimLevel
from loscr.hashing import canonical_hash
from loscr.models import CheckerResult, ClaimContract, ClaimReducerOutput, IncidentNode


def claim_reducer(
    contracts: Sequence[ClaimContract | dict[str, object]],
    checker_results: Sequence[CheckerResult | dict[str, object]],
    incidents: Sequence[IncidentNode | dict[str, object]] | None = None,
) -> ClaimReducerOutput:
    """Reduce contracts, checker results, and incidents into current claim state."""
    del incidents
    parsed_contracts = [
        item if isinstance(item, ClaimContract) else ClaimContract.model_validate(item)
        for item in contracts
    ]
    parsed_results = [
        item if isinstance(item, CheckerResult) else CheckerResult.model_validate(item)
        for item in checker_results
    ]

    requested_levels: dict[str, ClaimLevel] = {}
    sealed_epochs: dict[str, str] = {}
    supported_levels: dict[str, ClaimLevel] = {}
    quarantined_claims: set[str] = set()

    for contract in sorted(parsed_contracts, key=lambda item: (item.contract_epoch, item.claim_id)):
        requested_levels[contract.claim_id] = contract.claim_level
        sealed_epochs[contract.claim_id] = contract.contract_epoch

    for result in sorted(parsed_results, key=lambda item: (item.checked_at, item.check_id)):
        supported_levels[result.claim_id] = result.supported_level
        if result.status == CheckerStatus.QUARANTINED:
            quarantined_claims.add(result.claim_id)
        elif result.claim_id in quarantined_claims and result.status == CheckerStatus.VALID:
            quarantined_claims.remove(result.claim_id)

    output = ClaimReducerOutput(
        requested_levels=dict(sorted(requested_levels.items())),
        sealed_epochs=dict(sorted(sealed_epochs.items())),
        supported_levels=dict(sorted(supported_levels.items())),
        quarantined_claims=sorted(quarantined_claims),
    )
    return output.model_copy(update={"output_hash": canonical_hash(output)})
