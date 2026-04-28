from __future__ import annotations

from loscr.checker import CheckerContext, check
from loscr.models import DependencyReducerOutput, ServiceReducerOutput, TelemetryReducerOutput


def test_baseline_contamination_downgrades_production(make_contract, make_baseline, make_evaluator) -> None:  # type: ignore[no-untyped-def]
    contract = make_contract(
        claim_level="production_operational",
        baseline_ids=["base"],
        evaluator_ids=["eval"],
        evaluator_state_floor="audited",
        ledger_schema_ids=[
            "edge_events",
            "gate_ledger",
            "wip_ledger",
            "resource_ledger",
            "service_ledger",
            "service_obligations",
            "service_load_contracts",
            "audit_ledger",
            "delayed_label_ledger",
            "baseline_registry",
            "dependency_graph",
            "checker_results",
        ],
        service_envelopes=["validation|ci|normal"],
    )
    context = CheckerContext(
        telemetry=TelemetryReducerOutput(coverage_by_scope={"scope": 1.0}),
        service=ServiceReducerOutput(contract_states={"validation|ci|normal|edit": "active"}),
        ledgers_present=contract.ledger_schema_ids,
        evaluator_health={"eval": make_evaluator()},
        baseline_registry={"base": make_baseline(contaminated=True)},
        dependency=DependencyReducerOutput(unknown_dependency_fraction_by_claim={"claim": 0.0}),
    )
    result = check(contract, context)
    assert result.status.value == "downgraded"
    assert result.supported_level.value == "audited"
    assert any(code.family.value == "baseline" for code in result.failure_codes)
