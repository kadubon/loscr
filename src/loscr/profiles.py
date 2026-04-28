"""Canonical LOSCR claim profiles."""

from __future__ import annotations

from functools import lru_cache

from loscr.enums import ClaimForm, ClaimLevel, EvaluatorState, ServiceContractState
from loscr.models import ClaimLevelProfile


OBSERVABLE_EVENT_FIELDS: tuple[str, ...] = (
    "event_id",
    "event_type",
    "timestamp",
    "item_id",
    "parent_event_id",
    "station_id",
    "policy_id",
    "action_type",
    "substrate_fingerprint",
    "status_raw",
    "resource_raw",
    "queue_channel",
    "queue_age_raw",
    "dependency_flag",
    "reuse_count",
    "input_hash",
    "output_hash",
    "claim_scope_id",
    "integrity_hash",
)

IDENTIFIER_EVENT_FIELDS: tuple[str, ...] = (
    "event_id",
    "timestamp",
    "item_id",
    "parent_event_id",
    "station_id",
    "policy_id",
    "substrate_fingerprint",
    "input_hash",
    "output_hash",
    "claim_scope_id",
    "integrity_hash",
)

PRODUCTION_REQUIRED_CONTRACT_FIELDS: tuple[str, ...] = (
    "scope",
    "station_set",
    "task_strata",
    "freeze_rule",
    "downgrade_rule",
    "escalation_rule",
    "hard_constraints",
)

CAUSAL_REQUIRED_FIELDS: tuple[str, ...] = (
    "causal_design",
    "assignment_probability",
    "interference_handling",
    "exposure_mapping",
    "outcome_cap",
    "missingness_rule",
)


RAW_CANONICAL_PROFILES: dict[ClaimLevel, ClaimLevelProfile] = {
    ClaimLevel.DESCRIPTIVE: ClaimLevelProfile(
        claim_level=ClaimLevel.DESCRIPTIVE,
        telemetry_coverage_floor=0.0,
        downgrade_target=ClaimLevel.DESCRIPTIVE,
    ),
    ClaimLevel.OBSERVABLE: ClaimLevelProfile(
        claim_level=ClaimLevel.OBSERVABLE,
        required_event_fields=list(OBSERVABLE_EVENT_FIELDS),
        required_ledgers=["edge_events"],
        telemetry_coverage_floor=0.95,
        downgrade_target=ClaimLevel.DESCRIPTIVE,
    ),
    ClaimLevel.CONTROLLED: ClaimLevelProfile(
        claim_level=ClaimLevel.CONTROLLED,
        inherits=ClaimLevel.OBSERVABLE,
        required_ledgers=["edge_events", "gate_ledger", "wip_ledger", "resource_ledger"],
        required_contract_fields=list(PRODUCTION_REQUIRED_CONTRACT_FIELDS),
        downgrade_target=ClaimLevel.OBSERVABLE,
    ),
    ClaimLevel.SERVICE_CONTROLLED: ClaimLevelProfile(
        claim_level=ClaimLevel.SERVICE_CONTROLLED,
        inherits=ClaimLevel.CONTROLLED,
        required_ledgers=["service_ledger", "service_obligations", "service_load_contracts"],
        required_contract_fields=["service_envelopes"],
        service_contract_states=[ServiceContractState.ACTIVE, ServiceContractState.RECALIBRATED],
        telemetry_coverage_floor=0.95,
        downgrade_target=ClaimLevel.CONTROLLED,
    ),
    ClaimLevel.AUDITED: ClaimLevelProfile(
        claim_level=ClaimLevel.AUDITED,
        inherits=ClaimLevel.SERVICE_CONTROLLED,
        required_ledgers=["audit_ledger", "delayed_label_ledger"],
        evaluator_state_floor=EvaluatorState.MONITORED,
        telemetry_coverage_floor=0.98,
        downgrade_target=ClaimLevel.CONTROLLED,
    ),
    ClaimLevel.PRODUCTION_OPERATIONAL: ClaimLevelProfile(
        claim_level=ClaimLevel.PRODUCTION_OPERATIONAL,
        inherits=ClaimLevel.AUDITED,
        claim_form=ClaimForm.OPERATIONAL,
        required_ledgers=[
            "baseline_registry",
            "dependency_graph",
            "hard_constraint_ledger",
            "checker_results",
        ],
        evaluator_state_floor=EvaluatorState.AUDITED,
        telemetry_coverage_floor=0.99,
        baseline_requirements=["shadow_or_bridged_baseline", "contamination_test"],
        service_contract_states=[ServiceContractState.ACTIVE, ServiceContractState.RECALIBRATED],
        dependency_unknown_budget=0.01,
        downgrade_target=ClaimLevel.AUDITED,
    ),
    ClaimLevel.PRODUCTION_CAUSAL: ClaimLevelProfile(
        claim_level=ClaimLevel.PRODUCTION_CAUSAL,
        inherits=ClaimLevel.PRODUCTION_OPERATIONAL,
        claim_form=ClaimForm.CAUSAL,
        required_design=[
            "randomized_assignment_or_shadow_assignment_or_switchback_or_"
            "stepped_wedge_or_cluster_rollout_or_valid_instrument_or_bridge"
        ],
        required_logs=list(CAUSAL_REQUIRED_FIELDS),
        downgrade_target=ClaimLevel.PRODUCTION_OPERATIONAL,
    ),
    ClaimLevel.TRANSFER: ClaimLevelProfile(
        claim_level=ClaimLevel.TRANSFER,
        inherits=ClaimLevel.PRODUCTION_OPERATIONAL,
        claim_form=ClaimForm.TRANSFER,
        required_ledgers=["epoch_bridge_ledger"],
        bridge_requirements=["target_strata", "substrate_service", "evaluator"],
        dependency_unknown_budget=0.0,
        downgrade_target=ClaimLevel.PRODUCTION_OPERATIONAL,
    ),
    ClaimLevel.FRONTIER: ClaimLevelProfile(
        claim_level=ClaimLevel.FRONTIER,
        inherits=ClaimLevel.PRODUCTION_OPERATIONAL,
        claim_form=ClaimForm.FRONTIER,
        required_ledgers=["frontier_governance", "frontier_sampling_frames"],
        frontier_requirements=[
            "sealed_source",
            "quota",
            "weights",
            "blinding",
            "deduplication",
            "leakage_screen",
            "minimum_task_mass",
            "governance_contract",
        ],
        dependency_unknown_budget=0.0,
        downgrade_target=ClaimLevel.PRODUCTION_OPERATIONAL,
    ),
    ClaimLevel.REINVESTMENT: ClaimLevelProfile(
        claim_level=ClaimLevel.REINVESTMENT,
        inherits=ClaimLevel.PRODUCTION_CAUSAL,
        claim_form=ClaimForm.REINVESTMENT,
        required_ledgers=[
            "replay_record_ledger",
            "trusted_base_registry",
            "library_entries",
            "promotion_attribution",
            "reinvestment_edges",
        ],
        library_requirements=[
            "promoted_entries",
            "signed_lineage",
            "negative_lineage_audit",
            "causal_or_cohort_bounded_attribution",
            "finite_horizon_lower_bound",
        ],
        dependency_unknown_budget=0.0,
        downgrade_target=ClaimLevel.PRODUCTION_OPERATIONAL,
    ),
}


def _merge_unique(left: list[str], right: list[str]) -> list[str]:
    merged = list(left)
    for item in right:
        if item not in merged:
            merged.append(item)
    return merged


@lru_cache
def resolved_profile(level: ClaimLevel) -> ClaimLevelProfile:
    """Return a canonical profile with inherited requirements materialized."""
    profile = RAW_CANONICAL_PROFILES[level]
    if profile.inherits is None:
        return profile
    parent = resolved_profile(profile.inherits)
    return ClaimLevelProfile(
        claim_level=profile.claim_level,
        inherits=profile.inherits,
        claim_form=profile.claim_form or parent.claim_form,
        required_event_fields=_merge_unique(
            parent.required_event_fields, profile.required_event_fields
        ),
        required_contract_fields=_merge_unique(
            parent.required_contract_fields, profile.required_contract_fields
        ),
        required_ledgers=_merge_unique(parent.required_ledgers, profile.required_ledgers),
        allowed_estimators=_merge_unique(parent.allowed_estimators, profile.allowed_estimators),
        telemetry_coverage_floor=(
            profile.telemetry_coverage_floor
            if profile.telemetry_coverage_floor is not None
            else parent.telemetry_coverage_floor
        ),
        evaluator_state_floor=profile.evaluator_state_floor or parent.evaluator_state_floor,
        service_contract_states=profile.service_contract_states or parent.service_contract_states,
        dependency_unknown_budget=(
            profile.dependency_unknown_budget
            if profile.dependency_unknown_budget is not None
            else parent.dependency_unknown_budget
        ),
        baseline_requirements=_merge_unique(
            parent.baseline_requirements, profile.baseline_requirements
        ),
        frontier_requirements=_merge_unique(
            parent.frontier_requirements, profile.frontier_requirements
        ),
        library_requirements=_merge_unique(
            parent.library_requirements, profile.library_requirements
        ),
        hard_constraints=_merge_unique(parent.hard_constraints, profile.hard_constraints),
        bridge_requirements=_merge_unique(
            parent.bridge_requirements, profile.bridge_requirements
        ),
        required_design=_merge_unique(parent.required_design, profile.required_design),
        required_logs=_merge_unique(parent.required_logs, profile.required_logs),
        downgrade_target=profile.downgrade_target,
    )


def canonical_profiles() -> dict[str, ClaimLevelProfile]:
    """Return all resolved canonical profiles keyed by enum value."""
    return {level.value: resolved_profile(level) for level in RAW_CANONICAL_PROFILES}
