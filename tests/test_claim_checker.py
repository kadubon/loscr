from __future__ import annotations

from loscr.checker import CheckerContext, CheckerRegistries, check
from loscr.models import (
    DelayedLabelReducerOutput,
    DependencyReducerOutput,
    ServiceReducerOutput,
    TelemetryReducerOutput,
)


def test_checker_valid_controlled_claim(make_contract) -> None:  # type: ignore[no-untyped-def]
    contract = make_contract()
    context = CheckerContext(
        telemetry=TelemetryReducerOutput(coverage_by_scope={"scope": 1.0}),
        ledgers_present=["edge_events", "gate_ledger", "wip_ledger"],
        dependency=DependencyReducerOutput(),
    )
    result = check(contract, context, CheckerRegistries())
    assert result.status.value == "valid"
    assert result.supported_level.value == "controlled"
    assert result.integrity_hash.startswith("sha256:")


def test_checker_accepts_theory_ledger_aliases(make_contract) -> None:  # type: ignore[no-untyped-def]
    contract = make_contract(
        claim_level="production_operational",
        ledger_schema_ids=[
            "edge_log",
            "gate_ledger",
            "wip_ledger",
            "resource_ledger",
            "service_ledger",
            "service_obligation_ledger",
            "load_contract_ledger",
            "audit_ledger",
            "delayed_label_ledger",
            "baseline_registry",
            "dependency_graph",
            "checker_result_ledger",
        ],
        service_envelopes=["validation|ci|normal"],
    )
    context = CheckerContext(
        telemetry=TelemetryReducerOutput(coverage_by_scope={"scope": 1.0}),
        ledgers_present=[
            "edge_events",
            "gate_ledger",
            "wip_ledger",
            "resource_ledger",
            "service_ledger",
            "service_obligations",
            "service_load_contracts",
            "evaluator_health",
            "delayed_label_ledger",
            "dependency_graphs",
        ],
        dependency=DependencyReducerOutput(),
        service=ServiceReducerOutput(contract_states={"validation|ci|normal|edit": "active"}),
    )
    result = check(contract, context, CheckerRegistries())
    assert "required_ledger_missing" not in {item.code for item in result.failure_codes}


def test_audited_label_missing_assignment_probability_quarantines_evaluator_scope(
    make_contract,
) -> None:  # type: ignore[no-untyped-def]
    contract = make_contract(
        claim_level="audited",
        ledger_schema_ids=[
            "edge_events",
            "gate_ledger",
            "wip_ledger",
            "resource_ledger",
            "service_ledger",
            "service_obligations",
            "audit_ledger",
            "delayed_label_ledger",
        ],
    )
    context = CheckerContext(
        telemetry=TelemetryReducerOutput(coverage_by_scope={"scope": 1.0}),
        delayed_label=DelayedLabelReducerOutput(
            missing_assignment_probability_labels=["label-1"]
        ),
        ledgers_present=contract.ledger_schema_ids,
        dependency=DependencyReducerOutput(),
    )
    result = check(contract, context, CheckerRegistries())
    assert result.status.value == "quarantined"
    assert "unknown_assignment_probability" in {item.code for item in result.failure_codes}


def test_service_controlled_requires_load_contract(make_contract) -> None:  # type: ignore[no-untyped-def]
    contract = make_contract(
        claim_level="service_controlled",
        ledger_schema_ids=[
            "edge_events",
            "gate_ledger",
            "wip_ledger",
            "resource_ledger",
            "service_ledger",
            "service_obligations",
            "service_load_contracts",
        ],
        service_envelopes=["validation|ci|normal"],
    )
    context = CheckerContext(
        telemetry=TelemetryReducerOutput(coverage_by_scope={"scope": 1.0}),
        service=ServiceReducerOutput(),
        ledgers_present=contract.ledger_schema_ids,
        dependency=DependencyReducerOutput(),
    )
    result = check(contract, context, CheckerRegistries())
    assert result.status.value == "downgraded"
    assert result.supported_level.value == "controlled"
    assert "service_overload_or_contract_state" in {item.code for item in result.failure_codes}


def test_audited_missing_labels_require_missingness_rule(make_contract) -> None:  # type: ignore[no-untyped-def]
    contract = make_contract(
        claim_level="audited",
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
        ],
        service_envelopes=["validation|ci|normal"],
    )
    context = CheckerContext(
        telemetry=TelemetryReducerOutput(coverage_by_scope={"scope": 1.0}),
        service=ServiceReducerOutput(contract_states={"validation|ci|normal|edit": "active"}),
        delayed_label=DelayedLabelReducerOutput(missingness_by_claim={"claim": 0.5}),
        ledgers_present=contract.ledger_schema_ids,
        dependency=DependencyReducerOutput(),
    )
    result = check(contract, context, CheckerRegistries())
    assert result.status.value == "quarantined"
    assert "delayed_label_missingness_unhandled" in {item.code for item in result.failure_codes}
