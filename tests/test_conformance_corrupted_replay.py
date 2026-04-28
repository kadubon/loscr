from __future__ import annotations

from loscr.checker import CheckerContext, check
from loscr.models import DependencyReducerOutput, TelemetryReducerOutput


def test_corrupted_replay_quarantines_claim(make_contract) -> None:  # type: ignore[no-untyped-def]
    contract = make_contract(claim_level="production_operational", baseline_ids=["base"])
    context = CheckerContext(
        telemetry=TelemetryReducerOutput(coverage_by_scope={"scope": 1.0}),
        replay_corrupted=True,
        dependency=DependencyReducerOutput(),
    )
    result = check(contract, context)
    assert result.status.value == "quarantined"
    assert result.supported_level.value == "descriptive"
