"""Deterministic LOSCR claim checker."""

from __future__ import annotations

from typing import Iterable

from loscr.checker.context import CheckerContext, CheckerRegistries
from loscr.enums import (
    CheckerStatus,
    ClaimForm,
    ClaimLevel,
    EvaluatorState,
    FailureFamily,
    ServiceContractState,
    TrustedBaseState,
    level_gte,
)
from loscr.hashing import canonical_hash, compute_integrity_hash, verify_integrity_hash
from loscr.ledgers import normalize_ledger_names
from loscr.models import (
    BaselineRegistryEntry,
    CheckerResult,
    ClaimContract,
    DependencyReducerOutput,
    EpochBridge,
    EstimatorProfile,
    EvaluatorHealth,
    FailureCode,
    FrontierGovernanceContract,
    FrontierSamplingFrame,
    PromotionAttributionRecord,
    ReinvestmentLedgerEdge,
    SequentialMonitoringProfile,
    TrustedBaseEntry,
)
from loscr.profiles import CAUSAL_REQUIRED_FIELDS, resolved_profile
from loscr.transitions import cap_level, failure, status_for_failures

CHECKER_VERSION = "loscr-checker-v1"


def check(
    contract: ClaimContract,
    state: CheckerContext,
    registries: CheckerRegistries | None = None,
) -> CheckerResult:
    """Check a claim contract against reducer state and registries."""
    registries = registries or CheckerRegistries()
    failures: list[FailureCode] = []

    failures.extend(validate_schema_and_types(contract, state))
    failures.extend(verify_integrity_hashes(contract, state, registries))
    failures.extend(verify_contract_epoch_and_bridge(contract, state))
    failures.extend(reconstruct_state_from_append_only_events(state))
    failures.extend(apply_incident_scope_rule(contract, state))
    failures.extend(test_hard_constraints(contract, state))
    failures.extend(compute_telemetry_coverage(contract, state))
    failures.extend(test_claim_level_profile(contract.claim_level, contract, state, registries))
    failures.extend(test_claim_form_requirements(contract.claim_form, contract, state))
    failures.extend(test_service_reservations_and_age_envelopes(contract, state))
    failures.extend(test_evaluator_state_and_audit_age(contract, state))
    failures.extend(test_baseline_and_frontier_requirements(contract, state))
    failures.extend(test_dependency_coverage_and_boundary_certificates(contract, state))
    failures.extend(test_estimator_admissibility(contract, state))
    failures.extend(test_instrumentation_burden(contract, state))

    status = status_for_failures(failures)
    supported_level = cap_level(contract.claim_level, failures)
    if status == CheckerStatus.VALID and supported_level != contract.claim_level:
        status = CheckerStatus.DOWNGRADED

    dependency_hash = state.dependency_hash or canonical_hash(_dependency_payload(state))
    state_hash = state.state_hash or canonical_hash(state)
    checker_version_hash = canonical_hash({"checker_version": CHECKER_VERSION})
    supported_form = _supported_form(contract.claim_form, supported_level)
    violated_fields = sorted(
        {field for item in failures for field in item.violated_fields if field}
    )
    required_actions = sorted(
        {item.required_action for item in failures if item.required_action is not None}
    )
    incident_nodes = _incident_nodes_for_claim(contract.claim_id, state)
    base: dict[str, object] = {
        "check_id": "",
        "claim_id": contract.claim_id,
        "contract_epoch": contract.contract_epoch,
        "checked_at": state.prefix_time,
        "requested_level": contract.claim_level,
        "supported_level": supported_level,
        "supported_claim_form": supported_form,
        "status": status,
        "failure_codes": failures,
        "violated_fields": violated_fields,
        "incident_nodes": incident_nodes,
        "required_actions": required_actions,
        "frozen_intervals": sorted(state.frozen_intervals),
        "dependency_hash": dependency_hash,
        "state_hash": state_hash,
        "checker_version_hash": checker_version_hash,
        "integrity_hash": "",
    }
    check_id = canonical_hash({key: value for key, value in base.items() if key != "check_id"})
    base["check_id"] = check_id
    base["integrity_hash"] = compute_integrity_hash(base)
    return CheckerResult.model_validate(base)


def validate_schema_and_types(contract: ClaimContract, state: CheckerContext) -> list[FailureCode]:
    del state
    missing: list[str] = []
    for field in ["claim_id", "contract_epoch", "claim_level", "claim_form", "scope"]:
        value = getattr(contract, field)
        if value is None or value == "":
            missing.append(field)
    if missing:
        return [
            failure(
                FailureFamily.MISSING,
                "missing_identifier",
                "claim contract is missing required identifier fields",
                max_supported_level=ClaimLevel.DESCRIPTIVE,
                violated_fields=missing,
            )
        ]
    return []


def verify_integrity_hashes(
    contract: ClaimContract, state: CheckerContext, registries: CheckerRegistries
) -> list[FailureCode]:
    failures: list[FailureCode] = []
    if not verify_integrity_hash(contract):
        failures.append(
            failure(
                FailureFamily.INTEGRITY,
                "contract_integrity_failure",
                "claim contract integrity hash mismatch",
                violated_fields=["integrity_hash"],
            )
        )
    if state.telemetry.integrity_failures:
        failures.append(
            failure(
                FailureFamily.INTEGRITY,
                "edge_integrity_failure",
                "one or more edge events failed integrity verification",
                violated_fields=["edge_events.integrity_hash"],
            )
        )
    if state.service.integrity_failures:
        failures.append(
            failure(
                FailureFamily.INTEGRITY,
                "service_integrity_failure",
                "one or more service-control records failed integrity verification",
                violated_fields=state.service.integrity_failures,
            )
        )
    if state.replay_corrupted or state.library.quarantined_entries:
        failures.append(
            failure(
                FailureFamily.INTEGRITY,
                "corrupted_replay",
                "a replay or library dependency is corrupted or quarantined",
                violated_fields=["replay_record.integrity_hash"],
            )
        )
    inactive_trusted = [
        item.trusted_base_id
        for item in _relevant_trusted_base_entries(contract, state, registries)
        if item.state != TrustedBaseState.ACTIVE
    ]
    if inactive_trusted and level_gte(contract.claim_level, ClaimLevel.PRODUCTION_OPERATIONAL):
        failures.append(
            failure(
                FailureFamily.INTEGRITY,
                "trusted_base_revoked_or_stale",
                "a relevant trusted-base registry entry is revoked, stale, or out of scope",
                violated_fields=sorted(inactive_trusted),
            )
        )
    return failures


def verify_contract_epoch_and_bridge(
    contract: ClaimContract, state: CheckerContext
) -> list[FailureCode]:
    failures: list[FailureCode] = []
    if state.unbridged_epoch_change:
        failures.append(
            failure(
                FailureFamily.EPOCH,
                "epoch_without_bridge",
                "material epoch change is pooled without a valid bridge",
                max_supported_level=ClaimLevel.DESCRIPTIVE,
            )
        )
    if contract.claim_level == ClaimLevel.TRANSFER or contract.claim_form == ClaimForm.TRANSFER:
        required = set(resolved_profile(ClaimLevel.TRANSFER).bridge_requirements)
        declared = set(contract.bridge_requirements)
        matching = [
            bridge
            for bridge in state.epoch_bridges.values()
            if bridge.target_epoch == contract.contract_epoch
        ]
        valid_bridge = any(_bridge_satisfies_transfer(contract, bridge, required) for bridge in matching)
        missing = sorted(required - declared)
        if missing or not valid_bridge:
            failures.append(
                failure(
                    FailureFamily.EPOCH,
                    "transfer_bridge_missing_or_incomplete",
                    "transfer or stronger claim lacks a valid epoch bridge for target strata, substrate/service, and evaluator comparability",
                    max_supported_level=ClaimLevel.PRODUCTION_OPERATIONAL,
                    violated_fields=missing or ["epoch_bridges"],
                )
            )
    return failures


def reconstruct_state_from_append_only_events(state: CheckerContext) -> list[FailureCode]:
    failures: list[FailureCode] = []
    if state.telemetry.parent_link_failures:
        failures.append(
            failure(
                FailureFamily.LEDGER,
                "parent_link_missing",
                "event parent link is not reconstructable from ledger prefix",
                violated_fields=["parent_event_id"],
            )
        )
    if state.telemetry.substrate_drift_scopes:
        failures.append(
            failure(
                FailureFamily.EPOCH,
                "substrate_drift_without_bridge",
                "substrate changed inside a scope without bridge evidence",
                max_supported_level=ClaimLevel.DESCRIPTIVE,
                violated_fields=["substrate_fingerprint"],
            )
        )
    return failures


def apply_incident_scope_rule(contract: ClaimContract, state: CheckerContext) -> list[FailureCode]:
    reachable = _incident_nodes_for_claim(contract.claim_id, state)
    if reachable:
        return [
            failure(
                FailureFamily.DEPENDENCY,
                "incident_reachable",
                "claim is reachable from an unresolved incident node",
                max_supported_level=ClaimLevel.DESCRIPTIVE,
            )
        ]
    return []


def test_hard_constraints(contract: ClaimContract, state: CheckerContext) -> list[FailureCode]:
    if contract.claim_id in state.hard_stop_claim_ids:
        return [
            failure(
                FailureFamily.HARD_CONSTRAINT,
                "hard_stop_reachable",
                "hard-stop gate is reachable from the claim scope",
                max_supported_level=ClaimLevel.DESCRIPTIVE,
            )
        ]
    return []


def compute_telemetry_coverage(contract: ClaimContract, state: CheckerContext) -> list[FailureCode]:
    failures: list[FailureCode] = []
    if state.telemetry.missing_identifier_events:
        failures.append(
            failure(
                FailureFamily.MISSING,
                "missing_identifier",
                "identifier fields are missing in Layer 0 telemetry",
                max_supported_level=ClaimLevel.DESCRIPTIVE,
                violated_fields=["edge_events.identifier"],
            )
        )
    if state.delayed_label.missing_assignment_probability_labels and level_gte(
        contract.claim_level, ClaimLevel.AUDITED
    ):
        failures.append(
            failure(
                FailureFamily.EVALUATOR,
                "unknown_assignment_probability",
                "delayed labels used for audited or stronger claims lack logged assignment probability",
                max_supported_level=ClaimLevel.CONTROLLED,
                violated_fields=state.delayed_label.missing_assignment_probability_labels,
            )
        )
    missingness = state.delayed_label.missingness_by_claim.get(contract.claim_id, 0.0)
    if missingness > 0 and level_gte(contract.claim_level, ClaimLevel.AUDITED):
        if not _has_contract_value(contract, "missingness_rule"):
            failures.append(
                failure(
                    FailureFamily.EVALUATOR,
                    "delayed_label_missingness_unhandled",
                    "delayed labels have missing or censored outcomes without a declared missingness rule",
                    max_supported_level=ClaimLevel.CONTROLLED,
                    violated_fields=["missingness_rule"],
                )
            )
    profile = resolved_profile(contract.claim_level)
    floor = contract.telemetry_coverage_floor
    if floor is None:
        floor = profile.telemetry_coverage_floor or 0.0
    coverage = state.telemetry.coverage_by_scope.get(contract.scope, 0.0)
    if contract.claim_level != ClaimLevel.DESCRIPTIVE and coverage < floor:
        failures.append(
            failure(
                FailureFamily.PROFILE,
                "telemetry_coverage_below_floor",
                f"telemetry coverage {coverage:.4f} is below floor {floor:.4f}",
                max_supported_level=ClaimLevel.OBSERVABLE,
                violated_fields=["telemetry_coverage_floor"],
            )
        )
    return failures


def test_claim_level_profile(
    level: ClaimLevel,
    contract: ClaimContract,
    state: CheckerContext,
    registries: CheckerRegistries,
) -> list[FailureCode]:
    del registries
    profile = resolved_profile(level)
    failures: list[FailureCode] = []
    missing_contract_fields = [
        field
        for field in profile.required_contract_fields
        if not _has_contract_value(contract, field)
    ]
    if missing_contract_fields:
        failures.append(
            failure(
                FailureFamily.PROFILE,
                "required_contract_field_missing",
                "claim-level profile requires fields that are absent",
                max_supported_level=profile.downgrade_target or ClaimLevel.OBSERVABLE,
                violated_fields=missing_contract_fields,
            )
        )

    ledgers_present = normalize_ledger_names(state.ledgers_present) | normalize_ledger_names(
        contract.ledger_schema_ids
    )
    material_required_ledgers = _material_required_ledgers_for_level(level, profile.required_ledgers)
    missing_ledgers = sorted(normalize_ledger_names(material_required_ledgers) - ledgers_present)
    if missing_ledgers:
        failures.append(
            failure(
                FailureFamily.LEDGER,
                "required_ledger_missing",
                "claim-level profile requires ledgers that are absent",
                max_supported_level=profile.downgrade_target or ClaimLevel.CONTROLLED,
                violated_fields=missing_ledgers,
            )
        )
    return failures


def test_claim_form_requirements(
    claim_form: ClaimForm, contract: ClaimContract, state: CheckerContext
) -> list[FailureCode]:
    failures: list[FailureCode] = []
    needs_causal_design = (
        claim_form == ClaimForm.CAUSAL
        or contract.claim_level in {ClaimLevel.PRODUCTION_CAUSAL, ClaimLevel.REINVESTMENT}
    )
    if not needs_causal_design and contract.claim_level != ClaimLevel.REINVESTMENT:
        return failures
    missing = [field for field in CAUSAL_REQUIRED_FIELDS if not _has_contract_value(contract, field)]
    if missing:
        failures.append(
            failure(
                FailureFamily.ESTIMATOR,
                "missing_causal_design",
                "causal claim is missing design or log requirements",
                max_supported_level=ClaimLevel.PRODUCTION_OPERATIONAL,
                violated_fields=missing,
            )
        )
    if contract.claim_level == ClaimLevel.REINVESTMENT or claim_form == ClaimForm.REINVESTMENT:
        failures.extend(_test_reinvestment_requirements(contract, state))
    return failures


def test_service_reservations_and_age_envelopes(
    contract: ClaimContract, state: CheckerContext
) -> list[FailureCode]:
    if not level_gte(contract.claim_level, ClaimLevel.SERVICE_CONTROLLED):
        return []
    invalid_states = [
        key
        for key, value in state.service.contract_states.items()
        if value not in {ServiceContractState.ACTIVE, ServiceContractState.RECALIBRATED}
    ]
    missing_contracts = list(state.service.missing_contracts)
    if not state.service.contract_states:
        missing_contracts.append("service_load_contracts")
    if invalid_states or state.service.overloaded_queues or missing_contracts:
        return [
            failure(
                FailureFamily.SERVICE,
                "service_overload_or_contract_state",
                "service reservation, age envelope, or contract state blocks strong credit",
                max_supported_level=ClaimLevel.CONTROLLED,
                violated_fields=sorted(
                    invalid_states + state.service.overloaded_queues + missing_contracts
                ),
            )
        ]
    return []


def test_evaluator_state_and_audit_age(
    contract: ClaimContract, state: CheckerContext
) -> list[FailureCode]:
    if not level_gte(contract.claim_level, ClaimLevel.AUDITED):
        return []
    floor = contract.evaluator_state_floor or resolved_profile(contract.claim_level).evaluator_state_floor
    if floor is None:
        floor = EvaluatorState.MONITORED
    evaluators = _contract_evaluators(contract, state.evaluator_health.values())
    if not evaluators:
        return [
            failure(
                FailureFamily.EVALUATOR,
                "missing_evaluator_state",
                "audited or stronger claim requires evaluator state evidence",
                max_supported_level=ClaimLevel.CONTROLLED,
                violated_fields=["evaluator_ids"],
            )
        ]
    invalid: list[str] = []
    for evaluator in evaluators:
        if evaluator.state == EvaluatorState.REVOKED or evaluator.unresolved_incidents:
            invalid.append(evaluator.evaluator_id)
            continue
        if not _evaluator_meets_floor(evaluator, floor):
            invalid.append(evaluator.evaluator_id)
            continue
        if floor in {EvaluatorState.AUDITED, EvaluatorState.BRIDGED} and evaluator.audit_age_windows > 1:
            invalid.append(evaluator.evaluator_id)
        elif floor == EvaluatorState.MONITORED and evaluator.audit_age_windows > 2:
            invalid.append(evaluator.evaluator_id)
    if invalid:
        return [
            failure(
                FailureFamily.EVALUATOR,
                "evaluator_below_floor_or_stale",
                "evaluator is revoked, below floor, incident-affected, or stale",
                max_supported_level=ClaimLevel.CONTROLLED,
                violated_fields=sorted(invalid),
            )
        ]
    return []


def test_baseline_and_frontier_requirements(
    contract: ClaimContract, state: CheckerContext
) -> list[FailureCode]:
    failures: list[FailureCode] = []
    if level_gte(contract.claim_level, ClaimLevel.PRODUCTION_OPERATIONAL):
        baselines = [state.baseline_registry.get(item) for item in contract.baseline_ids]
        if not baselines or any(item is None for item in baselines):
            failures.append(
                failure(
                    FailureFamily.BASELINE,
                    "baseline_missing",
                    "production or stronger claim requires a baseline registry entry",
                    max_supported_level=ClaimLevel.AUDITED,
                    violated_fields=["baseline_ids"],
                )
            )
        else:
            bad = [item.baseline_id for item in baselines if item is not None and _bad_baseline(item)]
            if bad:
                failures.append(
                    failure(
                        FailureFamily.BASELINE,
                        "baseline_contamination_or_debt",
                        "baseline is contaminated, unbridged, or missing contamination test",
                        max_supported_level=ClaimLevel.AUDITED,
                        violated_fields=bad,
                    )
                )
    if level_gte(contract.claim_level, ClaimLevel.FRONTIER):
        if not contract.frontier_source_ids:
            failures.append(
                failure(
                    FailureFamily.FRONTIER,
                    "frontier_source_missing",
                    "frontier claim requires at least one sealed source identifier",
                    max_supported_level=ClaimLevel.PRODUCTION_OPERATIONAL,
                    violated_fields=["frontier_source_ids"],
                )
            )
            return failures
        missing_sources = [
            source_id
            for source_id in contract.frontier_source_ids
            if source_id not in state.frontier_governance
            or source_id not in state.frontier_sampling_frames
            or not state.frontier_governance[source_id].leakage_screen
            or not state.frontier_sampling_frames[source_id].leakage_screen
            or not _frontier_source_admissible(
                contract,
                state.frontier_governance.get(source_id),
                state.frontier_sampling_frames.get(source_id),
            )
        ]
        if missing_sources:
            failures.append(
                failure(
                    FailureFamily.FRONTIER,
                    "frontier_governance_missing_or_failed",
                    "frontier claim lacks sealed governance or sampling frame evidence",
                    max_supported_level=ClaimLevel.PRODUCTION_OPERATIONAL,
                    violated_fields=missing_sources,
                )
            )
    return failures


def test_dependency_coverage_and_boundary_certificates(
    contract: ClaimContract, state: CheckerContext
) -> list[FailureCode]:
    dependency = _dependency_output(state)
    if dependency is None:
        if level_gte(contract.claim_level, ClaimLevel.PRODUCTION_OPERATIONAL):
            return [
                failure(
                    FailureFamily.DEPENDENCY,
                    "dependency_graph_missing",
                    "production or stronger claim requires dependency graph coverage",
                    max_supported_level=ClaimLevel.AUDITED,
                )
            ]
        return []
    unknown_fraction = dependency.unknown_dependency_fraction_by_claim.get(contract.claim_id, 0.0)
    budget = resolved_profile(contract.claim_level).dependency_unknown_budget
    if budget is not None and unknown_fraction > budget:
        return [
            failure(
                FailureFamily.DEPENDENCY,
                "unknown_dependency_budget_exceeded",
                "unknown dependency fraction exceeds the canonical budget",
                max_supported_level=ClaimLevel.AUDITED,
                violated_fields=["dependency_unknown_budget"],
            )
        ]
    if dependency.expanded_boundaries and level_gte(contract.claim_level, ClaimLevel.PRODUCTION_OPERATIONAL):
        return [
            failure(
                FailureFamily.DEPENDENCY,
                "boundary_certificate_invalid_or_stale",
                "compressed dependency boundary is missing, stale, or invalid",
                max_supported_level=ClaimLevel.AUDITED,
                violated_fields=dependency.expanded_boundaries,
            )
        ]
    return []


def test_estimator_admissibility(contract: ClaimContract, state: CheckerContext) -> list[FailureCode]:
    if contract.claim_level not in {ClaimLevel.PRODUCTION_CAUSAL, ClaimLevel.REINVESTMENT} and (
        contract.claim_form != ClaimForm.CAUSAL
    ):
        return []
    missing = [field for field in CAUSAL_REQUIRED_FIELDS if not _has_contract_value(contract, field)]
    if missing:
        return [
            failure(
                FailureFamily.ESTIMATOR,
                "estimator_profile_failure",
                "causal estimator requirements are not satisfied",
                max_supported_level=ClaimLevel.PRODUCTION_OPERATIONAL,
                violated_fields=missing,
            )
        ]
    if not contract.estimator_profile_id:
        return [
            failure(
                FailureFamily.ESTIMATOR,
                "estimator_profile_missing",
                "causal or reinvestment claim requires a declared estimator profile",
                max_supported_level=ClaimLevel.PRODUCTION_OPERATIONAL,
                violated_fields=["estimator_profile_id"],
            )
        ]
    profile = state.estimator_profiles.get(contract.estimator_profile_id)
    if profile is None:
        return [
            failure(
                FailureFamily.ESTIMATOR,
                "estimator_profile_missing",
                "estimator profile is absent from the local ledger prefix",
                max_supported_level=ClaimLevel.PRODUCTION_OPERATIONAL,
                violated_fields=["estimator_profiles"],
            )
        ]
    if not verify_integrity_hash(profile):
        return [
            failure(
                FailureFamily.INTEGRITY,
                "estimator_profile_integrity_failure",
                "estimator profile integrity hash mismatch",
                violated_fields=["estimator_profile.integrity_hash"],
            )
        ]
    profile_violations = _estimator_profile_violations(profile, contract)
    if profile_violations:
        return [
            failure(
                FailureFamily.ESTIMATOR,
                "estimator_profile_failure",
                "estimator profile is missing assignment, positivity, outcome, or leakage diagnostics",
                max_supported_level=profile.max_claim_level_on_fail,
                violated_fields=profile_violations,
            )
        ]
    missing_logs = sorted(normalize_ledger_names(profile.required_logs) - normalize_ledger_names(
        contract.ledger_schema_ids + state.ledgers_present
    ))
    if missing_logs:
        return [
            failure(
                FailureFamily.ESTIMATOR,
                "estimator_required_logs_missing",
                "estimator profile requires logs that are absent from the ledger prefix",
                max_supported_level=profile.max_claim_level_on_fail,
                violated_fields=missing_logs,
            )
        ]
    if not _estimator_diagnostics_pass(profile.diagnostics):
        return [
            failure(
                FailureFamily.ESTIMATOR,
                "estimator_diagnostics_failed",
                "estimator diagnostics are missing or failed",
                max_supported_level=profile.max_claim_level_on_fail,
                violated_fields=["estimator_profile.diagnostics"],
            )
        ]
    if not level_gte(profile.max_claim_level_on_pass, contract.claim_level):
        return [
            failure(
                FailureFamily.ESTIMATOR,
                "estimator_profile_cap_exceeded",
                "estimator profile pass cap is weaker than the requested claim level",
                max_supported_level=profile.max_claim_level_on_pass,
                violated_fields=["estimator_profile.max_claim_level_on_pass"],
            )
        ]
    return []


def test_instrumentation_burden(
    contract: ClaimContract, state: CheckerContext
) -> list[FailureCode]:
    failures: list[FailureCode] = []
    if state.instrumentation_burden_exceeded and not contract.instrumentation_burden_charged:
        failures.append(
            failure(
                FailureFamily.BURDEN,
                "instrumentation_burden_uncharged",
                "instrumentation burden exceeded the ceiling without charge",
                max_supported_level=ClaimLevel.PRODUCTION_OPERATIONAL,
            )
        )
    if state.frozen_intervals and level_gte(contract.claim_level, ClaimLevel.PRODUCTION_OPERATIONAL):
        sequential = state.sequential_profiles.get(contract.claim_id)
        if not contract.freeze_rule or sequential is None:
            failures.append(
                failure(
                    FailureFamily.FREEZE,
                    "freeze_without_sequential_profile",
                    "frozen intervals require a sealed sequential monitoring profile",
                    max_supported_level=ClaimLevel.CONTROLLED,
                    violated_fields=["freeze_rule", "sequential_profiles"],
                )
            )
        elif not verify_integrity_hash(sequential):
            failures.append(
                failure(
                    FailureFamily.INTEGRITY,
                    "sequential_profile_integrity_failure",
                    "sequential monitoring profile integrity hash mismatch",
                    violated_fields=["sequential_profile.integrity_hash"],
                )
            )
        elif not _sequential_profile_admissible(sequential):
            failures.append(
                failure(
                    FailureFamily.FREEZE,
                    "sequential_monitoring_profile_invalid",
                    "sequential monitoring profile has inadmissible caps or diagnostics",
                    max_supported_level=sequential.max_supported_claim_level_on_diagnostic_fail,
                    violated_fields=["sequential_profile"],
                )
            )
    return failures


def _bridge_satisfies_transfer(
    contract: ClaimContract, bridge: EpochBridge, required: set[str]
) -> bool:
    if bridge.target_epoch != contract.contract_epoch:
        return False
    if not level_gte(bridge.max_supported_claim_level, ClaimLevel.TRANSFER):
        return False
    if bridge.minimum_overlap is None or bridge.minimum_overlap <= 0:
        return False
    if bridge.accepted_error_bound is None:
        return False
    diagnostics = bridge.diagnostics
    for item in required:
        value = diagnostics.get(item)
        if value not in {True, "pass", "passed", "valid"}:
            return False
    return True


def _frontier_source_admissible(
    contract: ClaimContract,
    governance: FrontierGovernanceContract | None,
    frame: FrontierSamplingFrame | None,
) -> bool:
    if governance is None or frame is None:
        return False
    if not level_gte(governance.max_supported_claim_level, ClaimLevel.FRONTIER):
        return False
    if not governance.sealed_source:
        return False
    if not governance.weights_pre_outcome:
        return False
    if not governance.blinding_rule or not governance.blinding_rule.strip():
        return False
    if not governance.leakage_screen or not frame.leakage_screen:
        return False
    if frame.quota <= 0 or frame.minimum_task_mass <= 0 or frame.quota < frame.minimum_task_mass:
        return False
    if contract.minimum_task_mass is not None and frame.minimum_task_mass < contract.minimum_task_mass:
        return False
    required_text = [
        governance.admission_authority,
        governance.independence_rule,
        governance.weight_authority,
        governance.weight_audit_rule,
        governance.deduplication_rule,
        governance.quota_freeze_time,
        governance.dispute_rule,
        frame.task_source,
        frame.eligibility_rule,
    ]
    return all(item.strip() for item in required_text)


def _estimator_diagnostics_pass(diagnostics: dict[str, object]) -> bool:
    if not diagnostics:
        return False
    if diagnostics.get("failed") is True:
        return False
    for key in ("passed", "admissible", "valid"):
        if key in diagnostics:
            return diagnostics[key] in {True, "true", "pass", "passed", "valid"}
    return False


def _estimator_profile_violations(
    profile: EstimatorProfile, contract: ClaimContract
) -> list[str]:
    violations: list[str] = []
    if not profile.assignment_record:
        violations.append("estimator_profile.assignment_record")
    if profile.positivity_floor is None or profile.positivity_floor <= 0 or profile.positivity_floor > 1:
        violations.append("estimator_profile.positivity_floor")
    if not profile.outcome_cap:
        violations.append("estimator_profile.outcome_cap")
    if profile.variance_cap is not None and profile.variance_cap <= 0:
        violations.append("estimator_profile.variance_cap")
    method = str(profile.diagnostics.get("method", "")).strip().lower()
    if method in {"doubly_robust", "dr"}:
        if profile.diagnostics.get("outcome_model_no_leakage") not in {
            True,
            "true",
            "pass",
            "passed",
            "valid",
        }:
            violations.append("estimator_profile.diagnostics.outcome_model_no_leakage")
        residual_ok = profile.diagnostics.get("residual_diagnostics_passed") in {
            True,
            "true",
            "pass",
            "passed",
            "valid",
        }
        conservative_bounds = profile.diagnostics.get("conservative_bounds_recorded") in {
            True,
            "true",
            "pass",
            "passed",
            "valid",
        }
        if not (residual_ok or conservative_bounds):
            violations.append("estimator_profile.diagnostics.residual_or_bounds")
    if contract.claim_level == ClaimLevel.REINVESTMENT and profile.estimand != "finite_horizon_return":
        violations.append("estimator_profile.estimand")
    return violations


def _sequential_profile_admissible(profile: SequentialMonitoringProfile) -> bool:
    if profile.increment_cap <= 0:
        return False
    if profile.alpha <= 0 or profile.alpha >= 1:
        return False
    failing_terms = {"fail", "failed", "invalid", "not_admissible"}
    return profile.tail_diagnostic.strip().lower() not in failing_terms


def _test_reinvestment_requirements(
    contract: ClaimContract, state: CheckerContext
) -> list[FailureCode]:
    del contract
    failures: list[FailureCode] = []
    if not state.library.promoted_entries:
        failures.append(
            failure(
                FailureFamily.PROFILE,
                "reinvestment_promoted_entries_missing",
                "reinvestment claim requires promoted certified library entries",
                max_supported_level=ClaimLevel.PRODUCTION_OPERATIONAL,
                violated_fields=["library.promoted_entries"],
            )
        )
    if state.library.due_entries:
        failures.append(
            failure(
                FailureFamily.PROFILE,
                "library_maintenance_due",
                "reinvestment claim is blocked by due library maintenance",
                max_supported_level=ClaimLevel.PRODUCTION_OPERATIONAL,
                violated_fields=state.library.due_entries,
            )
        )
    lineage_failures = _lineage_integrity_failures(
        state.promotion_attribution, state.reinvestment_edges
    )
    if lineage_failures:
        failures.append(
            failure(
                FailureFamily.INTEGRITY,
                "lineage_integrity_failure",
                "promotion attribution or reinvestment lineage has invalid integrity",
                violated_fields=lineage_failures,
            )
        )
        return failures
    promoted = set(state.library.promoted_entries)
    bounded_promotions = [
        item
        for item in state.promotion_attribution
        if promoted.intersection(item.library_entry_ids)
        and item.attribution_class in {"individual", "cohort_bounded"}
        and item.marginal_ablation_design
        and item.signed_lineage
        and item.lineage_signature_hash
        and item.negative_lineage_audit
        and item.finite_horizon_lower_bound is not None
        and item.finite_horizon_lower_bound > 0
    ]
    bounded_edges = [
        item
        for item in state.reinvestment_edges
        if item.parent_entry_id in promoted
        and item.lower_bound_return > 0
        and (
            item.edge_kind == "causal"
            or item.attribution_class in {"individual", "cohort_bounded"}
        )
    ]
    if not bounded_promotions or not bounded_edges:
        failures.append(
            failure(
                FailureFamily.DEPENDENCY,
                "reinvestment_lineage_unbounded",
                "reinvestment claim requires signed lineage, negative lineage audit, bounded attribution, and finite-horizon lower bound",
                max_supported_level=ClaimLevel.PRODUCTION_OPERATIONAL,
                violated_fields=["promotion_attribution", "reinvestment_edges"],
            )
        )
    return failures


def _lineage_integrity_failures(
    promotions: list[PromotionAttributionRecord], edges: list[ReinvestmentLedgerEdge]
) -> list[str]:
    failed: list[str] = []
    failed.extend(item.promotion_id for item in promotions if not verify_integrity_hash(item))
    failed.extend(item.edge_id for item in edges if not verify_integrity_hash(item))
    return sorted(failed)


def _relevant_trusted_base_entries(
    contract: ClaimContract, state: CheckerContext, registries: CheckerRegistries
) -> list[TrustedBaseEntry]:
    entries = list(state.trusted_base_entries.values())
    if registries.trusted_base_registry is not None:
        entries.extend(registries.trusted_base_registry.entries)
    by_id = {entry.trusted_base_id: entry for entry in entries}
    return [
        entry
        for entry in by_id.values()
        if entry.scope in {contract.scope, "*", "global", "all"}
    ]


def _has_contract_value(contract: ClaimContract, field: str) -> bool:
    value = getattr(contract, field, None)
    if value is None:
        return False
    if value == "":
        return False
    if isinstance(value, (list, dict, set, tuple)) and len(value) == 0:
        return False
    return True


def _material_required_ledgers_for_level(level: ClaimLevel, required: Iterable[str]) -> list[str]:
    if level == ClaimLevel.CONTROLLED:
        return ["edge_events", "gate_ledger", "wip_ledger"]
    if level == ClaimLevel.SERVICE_CONTROLLED:
        return [
            "edge_events",
            "gate_ledger",
            "wip_ledger",
            "service_ledger",
            "service_obligations",
            "service_load_contracts",
        ]
    if level_gte(level, ClaimLevel.PRODUCTION_OPERATIONAL):
        return [
            item
            for item in required
            if item
            in {
                "edge_events",
                "edge_log",
                "gate_ledger",
                "wip_ledger",
                "resource_ledger",
                "service_ledger",
                "service_load_contracts",
                "service_obligation_ledger",
                "service_obligations",
                "service_capacity_envelopes",
                "audit_ledger",
                "evaluator_health",
                "delayed_label_ledger",
                "delayed_labels",
                "baseline_registry",
                "dependency_graph",
                "dependency_graphs",
                "epoch_bridge_ledger",
                "epoch_bridges",
                "frontier_governance",
                "frontier_sampling_frames",
                "replay_record_ledger",
                "replay_records",
                "trusted_base_registry",
                "library_entries",
                "promotion_attribution",
                "reinvestment_edges",
                "estimator_profile_ledger",
                "estimator_profiles",
                "sequential_monitoring_ledger",
                "sequential_profiles",
                "checker_results",
                "checker_result_ledger",
            }
        ]
    return list(required)


def _contract_evaluators(
    contract: ClaimContract, all_evaluators: Iterable[EvaluatorHealth]
) -> list[EvaluatorHealth]:
    if contract.evaluator_ids:
        return [item for item in all_evaluators if item.evaluator_id in set(contract.evaluator_ids)]
    return list(all_evaluators)


def _evaluator_meets_floor(evaluator: EvaluatorHealth, floor: EvaluatorState) -> bool:
    if evaluator.state == EvaluatorState.REVOKED:
        return False
    order = {
        EvaluatorState.UNTRUSTED: 0,
        EvaluatorState.MONITORED: 1,
        EvaluatorState.AUDITED: 2,
        EvaluatorState.BRIDGED: 3,
        EvaluatorState.REVOKED: -1,
    }
    return order[evaluator.state] >= order[floor]


def _bad_baseline(entry: BaselineRegistryEntry) -> bool:
    if entry.contaminated or not entry.contamination_test:
        return True
    if entry.baseline_type != "shadow" and entry.bridge_status != "passed":
        return True
    return entry.baseline_debt > 0.05


def _dependency_output(state: CheckerContext) -> DependencyReducerOutput | None:
    if state.dependency is None:
        return None
    if isinstance(state.dependency, DependencyReducerOutput):
        return state.dependency
    if isinstance(state.dependency, dict):
        return DependencyReducerOutput.model_validate(state.dependency)
    return None


def _incident_nodes_for_claim(claim_id: str, state: CheckerContext) -> list[str]:
    dependency = _dependency_output(state)
    if dependency is None:
        return []
    reachable: list[str] = []
    for incident_id, claim_ids in dependency.incident_reachable_claims.items():
        if claim_id in claim_ids:
            reachable.append(incident_id)
    return sorted(reachable)


def _dependency_payload(state: CheckerContext) -> object:
    dependency = _dependency_output(state)
    return dependency.model_dump(mode="json") if dependency is not None else {}


def _supported_form(requested: ClaimForm, supported_level: ClaimLevel) -> ClaimForm:
    if supported_level == ClaimLevel.DESCRIPTIVE:
        return ClaimForm.DESCRIPTIVE
    if supported_level == ClaimLevel.PRODUCTION_OPERATIONAL and requested == ClaimForm.CAUSAL:
        return ClaimForm.OPERATIONAL
    if supported_level == ClaimLevel.PRODUCTION_CAUSAL:
        return ClaimForm.CAUSAL
    if supported_level == ClaimLevel.TRANSFER:
        return ClaimForm.TRANSFER
    if supported_level == ClaimLevel.FRONTIER:
        return ClaimForm.FRONTIER
    if supported_level == ClaimLevel.REINVESTMENT:
        return ClaimForm.REINVESTMENT
    return requested
