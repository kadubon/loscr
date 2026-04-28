from __future__ import annotations

from loscr.checker import CheckerContext, check
from loscr.models import DependencyReducerOutput, TelemetryReducerOutput


def test_hard_stop_dependency_reachability_quarantines_claim(make_contract) -> None:  # type: ignore[no-untyped-def]
    contract = make_contract(claim_level="production_operational")
    dependency = DependencyReducerOutput(incident_reachable_claims={"inc-1": ["claim"]})
    context = CheckerContext(
        telemetry=TelemetryReducerOutput(coverage_by_scope={"scope": 1.0}),
        dependency=dependency,
    )
    result = check(contract, context)
    assert result.status.value == "quarantined"
    assert "inc-1" in result.incident_nodes
