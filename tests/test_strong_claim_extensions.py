from __future__ import annotations

from typing import Any

from loscr.checker import CheckerContext, CheckerRegistries, check
from loscr.enums import TrustedBaseState
from loscr.integrity import seal_model
from loscr.models import (
    DependencyReducerOutput,
    EstimatorProfile,
    FrontierGovernanceContract,
    FrontierSamplingFrame,
    LibraryReducerOutput,
    PromotionAttributionRecord,
    ReinvestmentLedgerEdge,
    ServiceReducerOutput,
    TelemetryReducerOutput,
    TrustedBaseEntry,
)


def _strong_context(make_evaluator: Any, make_baseline: Any, **overrides: Any) -> CheckerContext:
    extra_ledgers = overrides.pop("ledgers_present", [])
    data: dict[str, Any] = {
        "telemetry": TelemetryReducerOutput(coverage_by_scope={"scope": 1.0}),
        "ledgers_present": [
            "edge_events",
            "gate_ledger",
            "wip_ledger",
            "resource_ledger",
            "service_ledger",
            "service_obligations",
            "service_load_contracts",
            "evaluator_health",
            "delayed_label_ledger",
            "baseline_registry",
            "dependency_graphs",
            "checker_results",
        ],
        "dependency": DependencyReducerOutput(),
        "service": ServiceReducerOutput(
            contract_states={"validation|ci|normal|edit": "active"}
        ),
        "evaluator_health": {"eval": make_evaluator()},
        "baseline_registry": {"base": make_baseline()},
    }
    data["ledgers_present"] = sorted(set(data["ledgers_present"]) | set(extra_ledgers))
    data.update(overrides)
    return CheckerContext(**data)


def _strong_contract(make_contract: Any, **overrides: Any) -> Any:
    extra_ledgers = overrides.pop("ledger_schema_ids", [])
    data: dict[str, Any] = {
        "claim_level": "production_operational",
        "claim_form": "operational",
        "ledger_schema_ids": [
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
            "dependency_graphs",
            "checker_results",
        ],
        "service_envelopes": ["validation|ci|normal"],
        "baseline_ids": ["base"],
        "evaluator_ids": ["eval"],
    }
    data["ledger_schema_ids"] = sorted(set(data["ledger_schema_ids"]) | set(extra_ledgers))
    data.update(overrides)
    return make_contract(**data)


def _estimator(**overrides: Any) -> EstimatorProfile:
    data: dict[str, Any] = {
        "estimator_id": "est",
        "estimand": "finite_horizon_return",
        "required_logs": [],
        "assignment_record": "sealed_assignment",
        "positivity_floor": 0.05,
        "outcome_cap": "winsorized",
        "diagnostics": {"passed": True},
        "max_claim_level_on_pass": "reinvestment",
        "max_claim_level_on_fail": "production_operational",
        "integrity_hash": "",
    }
    data.update(overrides)
    return seal_model(EstimatorProfile.model_validate(data))


def _promotion(**overrides: Any) -> PromotionAttributionRecord:
    data: dict[str, Any] = {
        "promotion_id": "promo",
        "library_entry_ids": ["lib-1"],
        "dependency_graph_hash": "sha256:dependency",
        "attribution_class": "unattributed",
        "integrity_hash": "",
    }
    data.update(overrides)
    return seal_model(PromotionAttributionRecord.model_validate(data))


def _reinvestment_edge(**overrides: Any) -> ReinvestmentLedgerEdge:
    data: dict[str, Any] = {
        "edge_id": "edge",
        "parent_entry_id": "lib-1",
        "child_entry_id": "lib-2",
        "attribution_class": "unattributed",
        "lower_bound_return": 0.0,
        "edge_kind": "descriptive",
        "integrity_hash": "",
    }
    data.update(overrides)
    return seal_model(ReinvestmentLedgerEdge.model_validate(data))


def _trusted_base(**overrides: Any) -> TrustedBaseEntry:
    data: dict[str, Any] = {
        "trusted_base_id": "tb",
        "build_identifier": "checker-build",
        "scope": "scope",
        "state": TrustedBaseState.ACTIVE,
        "integrity_hash": "",
    }
    data.update(overrides)
    return seal_model(TrustedBaseEntry.model_validate(data))


def _frontier_governance(**overrides: Any) -> FrontierGovernanceContract:
    data: dict[str, Any] = {
        "source_id": "frontier-src",
        "admission_authority": "sealed",
        "independence_rule": "independent",
        "stakeholder_or_domain_scope": "synthetic",
        "weight_authority": "predeclared",
        "weight_audit_rule": "audited",
        "blinding_rule": "blind outcome labels until weights are frozen",
        "leakage_screen": True,
        "deduplication_rule": "hash",
        "quota_freeze_time": "2026-01-01T00:00:00Z",
        "update_cadence": "frozen",
        "dispute_rule": "manual-audit",
        "integrity_hash": "",
    }
    data.update(overrides)
    return seal_model(FrontierGovernanceContract.model_validate(data))


def _frontier_frame(**overrides: Any) -> FrontierSamplingFrame:
    data: dict[str, Any] = {
        "source_id": "frontier-src",
        "task_source": "sealed",
        "eligibility_rule": "predeclared",
        "quota": 50,
        "minimum_task_mass": 50,
        "leakage_screen": True,
    }
    data.update(overrides)
    return FrontierSamplingFrame.model_validate(data)


def test_transfer_missing_epoch_bridge_downgrades(
    make_contract: Any, make_evaluator: Any, make_baseline: Any
) -> None:
    contract = _strong_contract(
        make_contract,
        claim_level="transfer",
        claim_form="transfer",
        bridge_requirements=["target_strata", "substrate_service", "evaluator"],
        ledger_schema_ids=["epoch_bridges"],
    )
    context = _strong_context(
        make_evaluator,
        make_baseline,
        ledgers_present=["epoch_bridges", "baseline_registry", "dependency_graphs"],
    )
    result = check(contract, context, CheckerRegistries())
    assert result.status.value == "downgraded"
    assert result.supported_level.value == "production_operational"
    assert "transfer_bridge_missing_or_incomplete" in {item.code for item in result.failure_codes}


def test_frontier_missing_governance_downgrades(
    make_contract: Any, make_evaluator: Any, make_baseline: Any
) -> None:
    contract = _strong_contract(
        make_contract,
        claim_level="frontier",
        claim_form="frontier",
        frontier_source_ids=["frontier-src"],
        ledger_schema_ids=["frontier_governance", "frontier_sampling_frames"],
    )
    context = _strong_context(
        make_evaluator,
        make_baseline,
        ledgers_present=["frontier_governance", "frontier_sampling_frames"],
    )
    result = check(contract, context, CheckerRegistries())
    assert result.status.value == "downgraded"
    assert result.supported_level.value == "production_operational"
    assert "frontier_governance_missing_or_failed" in {item.code for item in result.failure_codes}


def test_causal_claim_missing_estimator_profile_downgrades(
    make_contract: Any, make_evaluator: Any, make_baseline: Any
) -> None:
    contract = _strong_contract(
        make_contract,
        claim_level="production_causal",
        claim_form="causal",
        causal_design="switchback",
        assignment_probability="logged",
        interference_handling="clustered",
        exposure_mapping="per_item",
        outcome_cap="bounded",
        missingness_rule="conservative",
    )
    result = check(contract, _strong_context(make_evaluator, make_baseline), CheckerRegistries())
    assert result.status.value == "downgraded"
    assert result.supported_level.value == "production_operational"
    assert "estimator_profile_missing" in {item.code for item in result.failure_codes}


def test_causal_claim_inadmissible_estimator_profile_downgrades(
    make_contract: Any, make_evaluator: Any, make_baseline: Any
) -> None:
    contract = _strong_contract(
        make_contract,
        claim_level="production_causal",
        claim_form="causal",
        causal_design="switchback",
        assignment_probability="logged",
        interference_handling="clustered",
        exposure_mapping="per_item",
        outcome_cap="bounded",
        missingness_rule="conservative",
        estimator_profile_id="est",
    )
    context = _strong_context(
        make_evaluator,
        make_baseline,
        estimator_profiles={
            "est": _estimator(positivity_floor=None, max_claim_level_on_fail="audited")
        },
    )
    result = check(contract, context, CheckerRegistries())
    assert result.status.value == "downgraded"
    assert result.supported_level.value == "audited"
    assert "estimator_profile_failure" in {item.code for item in result.failure_codes}


def test_reinvestment_unbounded_lineage_downgrades(
    make_contract: Any, make_evaluator: Any, make_baseline: Any
) -> None:
    contract = _strong_contract(
        make_contract,
        claim_level="reinvestment",
        claim_form="reinvestment",
        causal_design="switchback",
        assignment_probability="logged",
        interference_handling="clustered",
        exposure_mapping="per_item",
        outcome_cap="bounded",
        missingness_rule="conservative",
        estimator_profile_id="est",
        ledger_schema_ids=["replay_records", "trusted_base_registry", "library_entries"],
    )
    context = _strong_context(
        make_evaluator,
        make_baseline,
        ledgers_present=["replay_records", "trusted_base_registry", "library_entries"],
        estimator_profiles={"est": _estimator()},
        library=LibraryReducerOutput(promoted_entries=["lib-1"]),
        promotion_attribution=[_promotion()],
        reinvestment_edges=[_reinvestment_edge()],
    )
    result = check(contract, context, CheckerRegistries())
    assert result.status.value == "downgraded"
    assert result.supported_level.value == "production_operational"
    assert "reinvestment_lineage_unbounded" in {item.code for item in result.failure_codes}


def test_reinvestment_signed_bounded_lineage_can_be_supported(
    make_contract: Any, make_evaluator: Any, make_baseline: Any
) -> None:
    contract = _strong_contract(
        make_contract,
        claim_level="reinvestment",
        claim_form="reinvestment",
        causal_design="switchback",
        assignment_probability="logged",
        interference_handling="clustered",
        exposure_mapping="per_item",
        outcome_cap="bounded",
        missingness_rule="conservative",
        estimator_profile_id="est",
        frontier_source_ids=["frontier-src"],
        ledger_schema_ids=[
            "replay_records",
            "trusted_base_registry",
            "library_entries",
            "promotion_attribution",
            "reinvestment_edges",
            "frontier_governance",
            "frontier_sampling_frames",
        ],
    )
    context = _strong_context(
        make_evaluator,
        make_baseline,
        ledgers_present=[
            "replay_records",
            "trusted_base_registry",
            "library_entries",
            "promotion_attribution",
            "reinvestment_edges",
            "frontier_governance",
            "frontier_sampling_frames",
        ],
        estimator_profiles={"est": _estimator()},
        frontier_governance={"frontier-src": _frontier_governance()},
        frontier_sampling_frames={"frontier-src": _frontier_frame()},
        library=LibraryReducerOutput(promoted_entries=["lib-1"]),
        promotion_attribution=[
            _promotion(
                attribution_class="cohort_bounded",
                marginal_ablation_design="holdout",
                signed_lineage=True,
                lineage_signature_hash="sha256:lineage",
                negative_lineage_audit=True,
                finite_horizon_lower_bound=1.0,
            )
        ],
        reinvestment_edges=[
            _reinvestment_edge(
                attribution_class="cohort_bounded",
                lower_bound_return=1.0,
                edge_kind="causal",
            )
        ],
    )
    result = check(contract, context, CheckerRegistries())
    assert result.status.value == "valid"
    assert result.supported_level.value == "reinvestment"


def test_revoked_trusted_base_quarantines(
    make_contract: Any, make_evaluator: Any, make_baseline: Any
) -> None:
    contract = _strong_contract(make_contract)
    revoked = _trusted_base(state=TrustedBaseState.REVOKED)
    context = _strong_context(
        make_evaluator,
        make_baseline,
        trusted_base_entries={"tb": revoked},
    )
    result = check(contract, context, CheckerRegistries())
    assert result.status.value == "quarantined"
    assert result.supported_level.value == "descriptive"
    assert "trusted_base_revoked_or_stale" in {item.code for item in result.failure_codes}


def test_freeze_without_sequential_profile_downgrades(
    make_contract: Any, make_evaluator: Any, make_baseline: Any
) -> None:
    contract = _strong_contract(make_contract)
    context = _strong_context(make_evaluator, make_baseline, frozen_intervals=["claim"])
    result = check(contract, context, CheckerRegistries())
    assert result.status.value == "downgraded"
    assert result.supported_level.value == "controlled"
    assert "freeze_without_sequential_profile" in {item.code for item in result.failure_codes}
