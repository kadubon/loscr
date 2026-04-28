from __future__ import annotations

from loscr.checker import CheckerContext, check
from loscr.models import DependencyReducerOutput, TelemetryReducerOutput


def test_stale_evaluator_quarantines_affected_strata(make_contract, make_evaluator) -> None:  # type: ignore[no-untyped-def]
    contract = make_contract(
        claim_level="audited",
        evaluator_ids=["eval"],
        evaluator_state_floor="audited",
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
        ledgers_present=[
            "edge_events",
            "gate_ledger",
            "wip_ledger",
            "service_ledger",
            "service_obligations",
            "audit_ledger",
            "delayed_label_ledger",
        ],
        evaluator_health={"eval": make_evaluator(audit_age_windows=9)},
        dependency=DependencyReducerOutput(),
    )
    result = check(contract, context)
    assert result.status.value == "quarantined"
    assert any(code.family.value == "evaluator" for code in result.failure_codes)
