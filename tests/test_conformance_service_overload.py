from __future__ import annotations

from loscr.checker import CheckerContext, check
from loscr.models import DependencyReducerOutput, ServiceReducerOutput, TelemetryReducerOutput


def test_service_overload_blocks_production_credit(make_contract) -> None:  # type: ignore[no-untyped-def]
    contract = make_contract(
        claim_level="service_controlled",
        ledger_schema_ids=[
            "edge_events",
            "gate_ledger",
            "wip_ledger",
            "service_ledger",
            "service_obligations",
        ],
    )
    context = CheckerContext(
        telemetry=TelemetryReducerOutput(coverage_by_scope={"scope": 1.0}),
        service=ServiceReducerOutput(overloaded_queues=["validation|ci|normal|w1"]),
        ledgers_present=[
            "edge_events",
            "gate_ledger",
            "wip_ledger",
            "service_ledger",
            "service_obligations",
        ],
        dependency=DependencyReducerOutput(),
    )
    result = check(contract, context)
    assert result.status.value == "downgraded"
    assert result.supported_level.value == "controlled"
