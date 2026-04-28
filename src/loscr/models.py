"""Pydantic data models for LOSCR ledgers, reducers, and checker output."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from loscr.enums import (
    CheckerStatus,
    ClaimForm,
    ClaimLevel,
    EvaluatorState,
    FailureFamily,
    FieldStatus,
    GateState,
    ItemState,
    LibraryState,
    ReplayTier,
    ServiceContractState,
    ServiceObligationStatus,
    TrustedBaseState,
)


class LoscrModel(BaseModel):
    """Base model that rejects undeclared fields."""

    model_config = ConfigDict(extra="forbid", use_enum_values=False, validate_assignment=True)


class ResourceRaw(LoscrModel):
    wall_time: float = 0.0
    compute_seconds: float = 0.0
    token_count: int = 0
    tool_call_count: int = 0


class ResourceLedgerEvent(LoscrModel):
    resource_event_id: str
    timestamp: str
    claim_scope_id: str
    item_id: str | None = None
    station_id: str | None = None
    resource_class: str = "generic"
    unit: str = "count"
    amount: float = 0.0
    charge_kind: Literal["resource", "instrumentation_burden", "service_burden"] = "resource"
    charged: bool = True
    source_event_id: str | None = None
    integrity_hash: str


class EdgeEventEnvelope(LoscrModel):
    event_id: str
    event_type: str
    timestamp: str
    item_id: str
    parent_event_id: str | None = None
    station_id: str
    policy_id: str
    action_type: str
    substrate_fingerprint: str
    status_raw: str
    resource_raw: ResourceRaw
    queue_channel: str
    queue_age_raw: float = 0.0
    dependency_flag: bool = False
    reuse_count: int = 0
    input_hash: str
    output_hash: str
    claim_scope_id: str
    integrity_hash: str


class FieldStatusRecord(LoscrModel):
    status: FieldStatus
    estimator_id: str | None = None
    error_bound: float | None = None


class EdgeEventSidecar(LoscrModel):
    event_source: str | None = None
    schema_id: str | None = None
    state_before_raw: dict[str, Any] | None = None
    state_after_raw: dict[str, Any] | None = None
    queue_id: str | None = None
    entered_queue_at: str | None = None
    left_queue_at: str | None = None
    adapter_id: str | None = None
    adapter_source_uri: str | None = None
    actor_process_id: str | None = None
    service_unit_id: str | None = None
    deadline_class: str | None = None
    baseline_assignment_id: str | None = None
    evaluator_id: str | None = None
    incident_id: str | None = None
    field_status_map: dict[str, FieldStatusRecord] = Field(default_factory=dict)
    integrity_hash: str | None = None


class AdapterContract(LoscrModel):
    adapter_id: str
    source_system: str
    source_event_type: str
    field_map: dict[str, str] = Field(default_factory=dict)
    missing_field_policy: str = "reject_or_descriptive"
    timestamp_policy: str = "source_timestamp_then_append_order"
    identity_policy: str = "stable_source_identifier"
    hash_policy: str = "hash_sensitive_content_by_default"
    privacy_filter: str = "no_raw_private_content_by_default"
    conformance_tests: list[str] = Field(default_factory=list)
    max_supported_claim_level: ClaimLevel = ClaimLevel.DESCRIPTIVE
    integrity_hash: str


class FailureCode(LoscrModel):
    family: FailureFamily
    code: str
    message: str
    max_supported_level: ClaimLevel | None = None
    violated_fields: list[str] = Field(default_factory=list)
    required_action: str | None = None


class ClaimLevelProfile(LoscrModel):
    claim_level: ClaimLevel
    inherits: ClaimLevel | None = None
    claim_form: ClaimForm | None = None
    required_event_fields: list[str] = Field(default_factory=list)
    required_contract_fields: list[str] = Field(default_factory=list)
    required_ledgers: list[str] = Field(default_factory=list)
    allowed_estimators: list[str] = Field(default_factory=list)
    telemetry_coverage_floor: float | None = None
    evaluator_state_floor: EvaluatorState | None = None
    service_contract_states: list[ServiceContractState] = Field(default_factory=list)
    dependency_unknown_budget: float | None = None
    baseline_requirements: list[str] = Field(default_factory=list)
    frontier_requirements: list[str] = Field(default_factory=list)
    library_requirements: list[str] = Field(default_factory=list)
    hard_constraints: list[str] = Field(default_factory=list)
    bridge_requirements: list[str] = Field(default_factory=list)
    required_design: list[str] = Field(default_factory=list)
    required_logs: list[str] = Field(default_factory=list)
    downgrade_target: ClaimLevel | None = None


class ClaimContract(LoscrModel):
    claim_id: str
    contract_epoch: str
    claim_level: ClaimLevel
    claim_form: ClaimForm = ClaimForm.OPERATIONAL
    scope: str
    station_set: list[str] = Field(default_factory=list)
    task_strata: list[str] = Field(default_factory=list)
    active_calendar_horizon: str | None = None
    minimum_task_mass: int | None = None
    minimum_service_exposure: float | None = None
    materiality_floor: float | None = None
    ledger_schema_ids: list[str] = Field(default_factory=list)
    baseline_ids: list[str] = Field(default_factory=list)
    frontier_source_ids: list[str] = Field(default_factory=list)
    allowed_evidence: list[str] = Field(default_factory=list)
    layer_activation_triggers: list[str] = Field(default_factory=list)
    telemetry_coverage_floor: float | None = None
    service_envelopes: list[str] = Field(default_factory=list)
    evaluator_state_floor: EvaluatorState | None = None
    uncertainty_rule: str | None = None
    bridge_requirements: list[str] = Field(default_factory=list)
    freeze_rule: str | None = None
    downgrade_rule: str | None = None
    escalation_rule: str | None = None
    owner: str | None = None
    sealed_at: str | None = None
    evaluator_ids: list[str] = Field(default_factory=list)
    hard_constraints: list[str] = Field(default_factory=list)
    causal_design: str | None = None
    assignment_probability: str | None = None
    interference_handling: str | None = None
    exposure_mapping: str | None = None
    outcome_cap: str | None = None
    missingness_rule: str | None = None
    estimator_profile_id: str | None = None
    instrumentation_burden_charged: bool = False
    integrity_hash: str


class EpochBridge(LoscrModel):
    bridge_id: str
    source_epoch: str
    target_epoch: str
    changed_fields: list[str] = Field(default_factory=list)
    bridge_design: str
    assignment_or_sampling_rule: str | None = None
    covered_strata: list[str] = Field(default_factory=list)
    minimum_overlap: float | None = None
    accepted_error_bound: float | None = None
    diagnostics: dict[str, Any] = Field(default_factory=dict)
    max_supported_claim_level: ClaimLevel = ClaimLevel.DESCRIPTIVE
    owner: str | None = None
    integrity_hash: str


class CheckerResult(LoscrModel):
    check_id: str
    claim_id: str
    contract_epoch: str
    checked_at: str
    requested_level: ClaimLevel
    supported_level: ClaimLevel
    supported_claim_form: ClaimForm
    status: CheckerStatus
    failure_codes: list[FailureCode] = Field(default_factory=list)
    violated_fields: list[str] = Field(default_factory=list)
    incident_nodes: list[str] = Field(default_factory=list)
    required_actions: list[str] = Field(default_factory=list)
    frozen_intervals: list[str] = Field(default_factory=list)
    dependency_hash: str
    state_hash: str
    checker_version_hash: str
    integrity_hash: str


class ServiceChannel(LoscrModel):
    channel: str
    unit: str
    control_window: str
    max_utilization: float = 1.0
    max_age: float = 0.0
    overload_action: str = "throttle"
    lower_service_rate: float = 0.0
    integrity_hash: str | None = None


class ServiceLedgerEvent(LoscrModel):
    service_event_id: str
    channel: str
    service_unit_id: str
    window_id: str
    unit: str
    deadline_class: str
    attempted: float = 0.0
    completed_accepted: float = 0.0
    completed_rejected: float = 0.0
    failed: float = 0.0
    cancelled: float = 0.0
    expired: float = 0.0
    held: float = 0.0
    unavailable_exposure: float = 0.0
    eligible_exposure: float = 0.0
    incident_id: str | None = None
    contract_id: str | None = None
    integrity_hash: str


class ServiceObligation(LoscrModel):
    obligation_id: str
    created_by_event_id: str
    claim_id: str
    channel: str
    service_unit_id: str
    deadline_class: str
    required_quantity: float = 0.0
    reserved_quantity: float = 0.0
    completed_quantity: float = 0.0
    cancelled_quantity: float = 0.0
    expired_quantity: float = 0.0
    held_quantity: float = 0.0
    created_at: str
    due_at: str
    queue_discipline: str = "earliest_deadline_first"
    priority_class: str = "normal"
    reservation_id: str | None = None
    status: ServiceObligationStatus = ServiceObligationStatus.CREATED
    integrity_hash: str


class ServiceLoadContract(LoscrModel):
    action_type: str
    substrate_scope: str
    service_unit_id: str
    channel: str
    deadline_class: str
    expected_load: float = 0.0
    upper_load: float = 0.0
    calibration_window: str
    minimum_observations: int = 30
    contract_state: ServiceContractState = ServiceContractState.DRAFT
    last_update_time: str | None = None
    violation_count: int = 0
    calibration_error: float = 0.0
    default_upper_bound: float = 0.0
    reservation_rule: str = "reserve_upper_load"
    max_supported_claim_level: ClaimLevel = ClaimLevel.DESCRIPTIVE
    integrity_hash: str


class ServiceCapacityEnvelope(LoscrModel):
    channel: str
    service_unit_id: str
    deadline_class: str
    steady: float = 0.0
    burst: float = 0.0
    age: float = 0.0
    window_id: str | None = None
    integrity_hash: str | None = None


class ServiceQueueState(LoscrModel):
    channel: str
    service_unit_id: str
    deadline_class: str
    window_id: str
    required: float = 0.0
    reserved: float = 0.0
    completed: float = 0.0
    cancelled: float = 0.0
    expired: float = 0.0
    held: float = 0.0
    outstanding: float = 0.0
    oldest_age: float = 0.0
    overloaded: bool = False


class ReplayRecord(LoscrModel):
    library_entry_id: str
    interface_signature: str
    contract_id: str
    checker_id: str
    trusted_base_id: str
    replay_tier: ReplayTier
    replay_codec_id: str
    witness_hash: str
    protected_trace_hash: str
    dependency_hashes: list[str] = Field(default_factory=list)
    validation_event_id: str
    maintenance_due_time: str
    retention_class: str
    integrity_hash: str


class TrustedBaseEntry(LoscrModel):
    trusted_base_id: str
    entry_type: str = "checker"
    build_identifier: str
    scope: str
    owner: str | None = None
    validation_method: str | None = None
    allowed_substrates: list[str] = Field(default_factory=list)
    revocation_condition: str | None = None
    bridge_rule: str | None = None
    last_audit_time: str | None = None
    audit_cadence: str | None = None
    state: TrustedBaseState = TrustedBaseState.ACTIVE
    integrity_hash: str


class TrustedBaseRegistry(LoscrModel):
    registry_id: str
    trust_root: str | None = None
    entries: list[TrustedBaseEntry] = Field(default_factory=list)
    registry_checker: str | None = None
    integrity_hash: str | None = None


class LibraryEntry(LoscrModel):
    library_entry_id: str
    interface_signature: str
    contract_id: str
    replay_record_id: str | None = None
    trusted_base_id: str | None = None
    state: LibraryState = LibraryState.CANDIDATE
    admission_time: str | None = None
    promotion_deadline: str | None = None
    maintenance_due_time: str | None = None
    owner: str | None = None
    integrity_hash: str | None = None


class PromotionAttributionRecord(LoscrModel):
    promotion_id: str
    library_entry_ids: list[str] = Field(default_factory=list)
    dependency_graph_hash: str
    co_use_set: list[str] = Field(default_factory=list)
    marginal_ablation_design: str | None = None
    attribution_class: Literal["individual", "cohort_bounded", "unattributed"] = "unattributed"
    interaction_penalty: float = 0.0
    service_load_attribution: dict[str, float] = Field(default_factory=dict)
    signed_lineage: bool = False
    lineage_signature_hash: str | None = None
    negative_lineage_audit: bool = False
    finite_horizon_lower_bound: float | None = None
    integrity_hash: str


class ReinvestmentLedgerEdge(LoscrModel):
    edge_id: str
    parent_entry_id: str
    child_entry_id: str
    delay: str | None = None
    service_charges: float = 0.0
    maintenance_charges: float = 0.0
    attribution_class: Literal["individual", "cohort_bounded", "unattributed"] = "unattributed"
    lower_bound_return: float = 0.0
    edge_kind: Literal["causal", "descriptive"] = "descriptive"
    integrity_hash: str


class EvaluatorAuditProfile(LoscrModel):
    evaluator_id: str
    target_strata: list[str] = Field(default_factory=list)
    alpha: float = 0.05
    known_good_min_count: int = 30
    known_bad_min_count: int = 30
    canary_min_count: int = 30
    shortcut_probe_min_count: int = 30
    blinded_review_min_count: int = 30
    lcb_method: str = "conservative"
    ucb_method: str = "conservative"
    canary_exposure_budget: float = 0.0
    leakage_probe_rule: str | None = None
    drift_test: str | None = None
    audit_cadence: str = "one_active_control_window"
    max_supported_claim_level_on_pass: ClaimLevel = ClaimLevel.AUDITED
    max_supported_claim_level_on_fail: ClaimLevel = ClaimLevel.CONTROLLED
    integrity_hash: str


class EvaluatorHealth(LoscrModel):
    evaluator_id: str
    state: EvaluatorState = EvaluatorState.UNTRUSTED
    target_strata: list[str] = Field(default_factory=list)
    known_good_pass_lcb: float = 0.0
    known_bad_reject_lcb: float = 0.0
    canary_integrity: bool = True
    shortcut_probe_failure_ucb: float = 0.0
    leakage_signal: bool = False
    blinded_review_disagreement_ucb: float = 0.0
    missingness: float = 0.0
    unresolved_incidents: list[str] = Field(default_factory=list)
    audit_age_windows: int = 0
    integrity_hash: str | None = None


class DelayedLabelRecord(LoscrModel):
    label_id: str
    item_id: str
    claim_id: str
    stratum: str
    evaluator_id: str
    assignment_probability: float | None = None
    assignment_time: str
    reveal_time: str | None = None
    observed_label: str | None = None
    missingness_state: Literal["observed", "missing", "censored"] = "observed"
    integrity_hash: str


class BaselineRegistryEntry(LoscrModel):
    baseline_id: str
    baseline_type: Literal["frozen", "rolling", "shadow", "external"] = "shadow"
    policy_identity: str
    substrate_fingerprint: str
    service_state: str | None = None
    tools: list[str] = Field(default_factory=list)
    permission_tier: str | None = None
    resource_caps: dict[str, float] = Field(default_factory=dict)
    update_time: str | None = None
    allowed_information: list[str] = Field(default_factory=list)
    task_eligibility: str | None = None
    assignment_rule: str | None = None
    contamination_test: bool = False
    known_limitations: list[str] = Field(default_factory=list)
    bridge_status: Literal["none", "passed", "failed"] = "none"
    contaminated: bool = False
    baseline_debt: float = 0.0
    integrity_hash: str | None = None


class BaselineUpdateContract(LoscrModel):
    baseline_id: str
    update_type: str
    reason: str
    sealed_before: str
    allowed_information: list[str] = Field(default_factory=list)
    excluded_information: list[str] = Field(default_factory=list)
    assignment_rule: str | None = None
    contamination_tests: list[str] = Field(default_factory=list)
    bridge_design: str | None = None
    maximum_update_frequency: str | None = None
    max_supported_claim_level: ClaimLevel = ClaimLevel.DESCRIPTIVE
    integrity_hash: str


class FrontierGovernanceContract(LoscrModel):
    source_id: str
    admission_authority: str
    independence_rule: str
    stakeholder_or_domain_scope: str
    weight_authority: str
    weight_audit_rule: str
    weights_pre_outcome: bool = True
    blinding_rule: str | None = None
    sealed_source: bool = True
    leakage_screen: bool = False
    deduplication_rule: str
    difficulty_strata: list[str] = Field(default_factory=list)
    quota_freeze_time: str
    update_cadence: str
    dispute_rule: str
    max_supported_claim_level: ClaimLevel = ClaimLevel.FRONTIER
    integrity_hash: str


class FrontierSamplingFrame(LoscrModel):
    source_id: str
    task_source: str
    eligibility_rule: str
    hardness_proxy: str | None = None
    stratum_labels: list[str] = Field(default_factory=list)
    quota: int
    minimum_task_mass: int = 50
    minimum_calendar_duration: str = "three_active_control_windows"
    leakage_screen: bool = False
    integrity_hash: str | None = None


class EstimatorProfile(LoscrModel):
    estimator_id: str
    estimand: str
    required_logs: list[str] = Field(default_factory=list)
    assignment_record: str | None = None
    positivity_floor: float | None = None
    outcome_cap: str | None = None
    clipping_rule: str | None = None
    variance_cap: float | None = None
    training_data_exclusions: list[str] = Field(default_factory=list)
    diagnostics: dict[str, Any] = Field(default_factory=dict)
    fallback_estimator: str | None = None
    max_claim_level_on_pass: ClaimLevel = ClaimLevel.AUDITED
    max_claim_level_on_fail: ClaimLevel = ClaimLevel.OBSERVABLE
    integrity_hash: str


class SequentialMonitoringProfile(LoscrModel):
    claim_id: str
    increment_definition: str
    increment_cap: float
    tail_family: str
    tail_diagnostic: str
    missingness_rule: str
    incident_handling_rule: str
    confidence_sequence_method: str
    alpha: float = 0.05
    review_interval: str
    freeze_trigger: str
    max_supported_claim_level_on_diagnostic_fail: ClaimLevel = ClaimLevel.CONTROLLED
    integrity_hash: str


class LoggedPropensityObservation(LoscrModel):
    observation_id: str
    stratum: str = "default"
    assignment_probability: float
    value: float
    audited: bool = True
    missing: bool = False
    censored: bool = False
    weight: float = 1.0
    outcome_model_value: float | None = None
    lower_value_bound: float | None = None
    upper_value_bound: float | None = None
    integrity_hash: str | None = None


class EstimatorResult(LoscrModel):
    estimator_id: str
    estimand: Literal["finite_window_total", "finite_window_mean"]
    estimate_total: float
    estimate_mean: float | None = None
    target_mass: float | None = None
    sample_count: int = 0
    used_count: int = 0
    missing_count: int = 0
    positivity_floor: float | None = None
    variance_upper_bound: float | None = None
    lower_bound: float | None = None
    upper_bound: float | None = None
    diagnostics: dict[str, Any] = Field(default_factory=dict)
    output_hash: str = ""


class AuditBoundInput(LoscrModel):
    accepted_value: float
    false_accept_upper_bound: float = 0.0
    leakage_upper_bound: float = 0.0
    missing_certifiedness_upper_bound: float = 0.0
    other_upper_bounds: dict[str, float] = Field(default_factory=dict)


class AuditBoundResult(LoscrModel):
    accepted_value: float
    certified_lower_bound: float
    components: dict[str, float] = Field(default_factory=dict)
    output_hash: str = ""


class EpsilonDominanceInput(LoscrModel):
    baseline_value: float
    candidate_value: float
    baseline_resource: float
    candidate_resource: float
    value_epsilon: float = 0.0
    resource_epsilon: float = 0.0
    gate_not_worse: bool = True
    wip_not_increased: bool = True
    library_liability_not_increased: bool = True


class EpsilonDominanceResult(LoscrModel):
    epsilon_dominates: bool
    value_margin: float
    resource_margin: float
    rate_improvement_margin: float | None = None
    blockers: list[str] = Field(default_factory=list)
    output_hash: str = ""


class RateImprovementResult(LoscrModel):
    baseline_rate: float
    delta_value: float
    delta_resource: float
    margin: float
    improves: bool
    output_hash: str = ""


class FiniteHorizonReinvestmentInput(LoscrModel):
    transition_lower_bound_matrix: list[list[float]]
    initial_vector: list[float]
    horizon: int
    include_initial: bool = False
    lower_bound_offset: float = 0.0


class FiniteHorizonReinvestmentResult(LoscrModel):
    horizon: int
    dimension: int
    per_step_totals: list[float] = Field(default_factory=list)
    terminal_vector: list[float] = Field(default_factory=list)
    lower_bound_total: float
    output_hash: str = ""


class ConfidenceSequenceResult(LoscrModel):
    method: str
    alpha: float
    cumulative_sum: float
    variance_upper_bound: float
    radius: float
    lower_bound: float
    output_hash: str = ""


class DependencyNode(LoscrModel):
    node_id: str
    node_type: str
    claim_scope_id: str | None = None
    gate_state: GateState = GateState.PASS
    integrity_hash: str | None = None


class DependencyEdge(LoscrModel):
    source: str
    target: str
    edge_type: str
    known: bool = True
    boundary_id: str | None = None
    integrity_hash: str | None = None


class BoundaryCertificate(LoscrModel):
    boundary_id: str
    included_node_types: list[str] = Field(default_factory=list)
    excluded_node_types: list[str] = Field(default_factory=list)
    upstream_sources: list[str] = Field(default_factory=list)
    downstream_claims: list[str] = Field(default_factory=list)
    owner: str | None = None
    audit_method: str | None = None
    last_audit_time: str | None = None
    expansion_rule: str = "root_scope"
    valid: bool = True
    stale: bool = False
    max_supported_claim_level: ClaimLevel = ClaimLevel.PRODUCTION_OPERATIONAL
    integrity_hash: str | None = None


class IncidentNode(LoscrModel):
    incident_id: str
    node_id: str
    incident_type: str
    gate_state: GateState = GateState.HARD_STOP
    affected_scope: str | None = None
    opened_at: str
    resolved_at: str | None = None
    integrity_hash: str | None = None


class GateLedgerEvent(LoscrModel):
    gate_event_id: str
    target_id: str
    target_type: str = "claim"
    claim_id: str | None = None
    claim_scope_id: str | None = None
    gate_state: GateState
    reason: str
    timestamp: str
    incident_id: str | None = None
    integrity_hash: str


class WipItemEvent(LoscrModel):
    item_event_id: str
    item_id: str
    claim_scope_id: str
    station_id: str
    stratum: str
    item_state: ItemState
    timestamp: str
    queue_age_raw: float = 0.0
    integrity_hash: str


class ExplorationBudgetEvent(LoscrModel):
    budget_event_id: str
    claim_id: str
    event_type: Literal["allocate", "charge", "release", "freeze"]
    resource_class: str = "generic"
    amount: float = 0.0
    timestamp: str
    reason: str | None = None
    integrity_hash: str


class DependencyGraph(LoscrModel):
    graph_id: str
    nodes: list[DependencyNode] = Field(default_factory=list)
    edges: list[DependencyEdge] = Field(default_factory=list)
    boundary_certificates: list[BoundaryCertificate] = Field(default_factory=list)
    integrity_hash: str | None = None


class RejectionRecord(LoscrModel):
    rejection_id: str
    source_ledger: str
    reason: str
    raw_record_hash: str
    created_at: str
    replay_inert: bool = True
    integrity_hash: str


class ReducerIssue(LoscrModel):
    family: FailureFamily
    code: str
    message: str
    event_id: str | None = None
    claim_id: str | None = None
    field: str | None = None


class TelemetryReducerOutput(LoscrModel):
    event_count: int = 0
    coverage_by_scope: dict[str, float] = Field(default_factory=dict)
    coverage_by_scope_station_stratum: dict[str, float] = Field(default_factory=dict)
    field_status_by_scope: dict[str, dict[str, FieldStatus]] = Field(default_factory=dict)
    missing_identifier_events: list[str] = Field(default_factory=list)
    integrity_failures: list[str] = Field(default_factory=list)
    parent_link_failures: list[str] = Field(default_factory=list)
    substrate_drift_scopes: list[str] = Field(default_factory=list)
    latest_event_time: str | None = None
    issues: list[ReducerIssue] = Field(default_factory=list)
    output_hash: str = ""


class ServiceReducerOutput(LoscrModel):
    queue_states: list[ServiceQueueState] = Field(default_factory=list)
    contract_states: dict[str, ServiceContractState] = Field(default_factory=dict)
    violation_counts: dict[str, int] = Field(default_factory=dict)
    uncalibrated_contracts: list[str] = Field(default_factory=list)
    suspect_contracts: list[str] = Field(default_factory=list)
    quarantined_contracts: list[str] = Field(default_factory=list)
    missing_contracts: list[str] = Field(default_factory=list)
    integrity_failures: list[str] = Field(default_factory=list)
    overloaded_queues: list[str] = Field(default_factory=list)
    output_hash: str = ""


class GateReducerOutput(LoscrModel):
    active_gate_states: dict[str, GateState] = Field(default_factory=dict)
    hard_stop_targets: list[str] = Field(default_factory=list)
    hard_stop_claim_ids: list[str] = Field(default_factory=list)
    quarantined_targets: list[str] = Field(default_factory=list)
    rollback_targets: list[str] = Field(default_factory=list)
    warned_targets: list[str] = Field(default_factory=list)
    incident_ids: list[str] = Field(default_factory=list)
    output_hash: str = ""


class WipReducerOutput(LoscrModel):
    unresolved_wip_by_scope: dict[str, int] = Field(default_factory=dict)
    unresolved_wip_by_scope_station_stratum: dict[str, int] = Field(default_factory=dict)
    max_queue_age_by_scope: dict[str, float] = Field(default_factory=dict)
    certified_items: list[str] = Field(default_factory=list)
    rejected_items: list[str] = Field(default_factory=list)
    expired_items: list[str] = Field(default_factory=list)
    quarantined_items: list[str] = Field(default_factory=list)
    output_hash: str = ""


class ExplorationReducerOutput(LoscrModel):
    remaining_budget_by_claim: dict[str, float] = Field(default_factory=dict)
    charges_by_claim: dict[str, float] = Field(default_factory=dict)
    frozen_claims: list[str] = Field(default_factory=list)
    output_hash: str = ""


class ResourceReducerOutput(LoscrModel):
    totals_by_scope_resource: dict[str, float] = Field(default_factory=dict)
    instrumentation_burden_by_scope: dict[str, float] = Field(default_factory=dict)
    uncharged_burden_scopes: list[str] = Field(default_factory=list)
    output_hash: str = ""


class DelayedLabelReducerOutput(LoscrModel):
    label_count_by_claim: dict[str, int] = Field(default_factory=dict)
    missing_assignment_probability_labels: list[str] = Field(default_factory=list)
    missingness_by_claim: dict[str, float] = Field(default_factory=dict)
    output_hash: str = ""


class PressureReducerOutput(LoscrModel):
    pressure_by_station: dict[str, float] = Field(default_factory=dict)
    bottleneck_stations: list[str] = Field(default_factory=list)
    output_hash: str = ""


class ArtifactReducerOutput(LoscrModel):
    artifact_count_by_scope: dict[str, int] = Field(default_factory=dict)
    dependency_flagged_artifacts: list[str] = Field(default_factory=list)
    output_hash: str = ""


class BaselineReducerOutput(LoscrModel):
    entries: dict[str, BaselineRegistryEntry] = Field(default_factory=dict)
    contaminated: list[str] = Field(default_factory=list)
    baseline_debt_by_id: dict[str, float] = Field(default_factory=dict)
    total_baseline_debt: float = 0.0
    output_hash: str = ""


class DependencyReducerOutput(LoscrModel):
    incident_reachable_claims: dict[str, list[str]] = Field(default_factory=dict)
    dependency_coverage_by_claim: dict[str, float] = Field(default_factory=dict)
    unknown_dependency_fraction_by_claim: dict[str, float] = Field(default_factory=dict)
    expanded_boundaries: list[str] = Field(default_factory=list)
    output_hash: str = ""


class LibraryReducerOutput(LoscrModel):
    states_by_entry: dict[str, LibraryState] = Field(default_factory=dict)
    quarantined_entries: list[str] = Field(default_factory=list)
    due_entries: list[str] = Field(default_factory=list)
    promoted_entries: list[str] = Field(default_factory=list)
    output_hash: str = ""


class ClaimReducerOutput(LoscrModel):
    requested_levels: dict[str, ClaimLevel] = Field(default_factory=dict)
    sealed_epochs: dict[str, str] = Field(default_factory=dict)
    supported_levels: dict[str, ClaimLevel] = Field(default_factory=dict)
    quarantined_claims: list[str] = Field(default_factory=list)
    output_hash: str = ""


class ReducerSnapshot(LoscrModel):
    telemetry: TelemetryReducerOutput = Field(default_factory=TelemetryReducerOutput)
    gate: GateReducerOutput = Field(default_factory=GateReducerOutput)
    wip: WipReducerOutput = Field(default_factory=WipReducerOutput)
    service: ServiceReducerOutput = Field(default_factory=ServiceReducerOutput)
    baseline: BaselineReducerOutput = Field(default_factory=BaselineReducerOutput)
    exploration: ExplorationReducerOutput = Field(default_factory=ExplorationReducerOutput)
    resource: ResourceReducerOutput = Field(default_factory=ResourceReducerOutput)
    delayed_label: DelayedLabelReducerOutput = Field(default_factory=DelayedLabelReducerOutput)
    pressure: PressureReducerOutput = Field(default_factory=PressureReducerOutput)
    artifact: ArtifactReducerOutput = Field(default_factory=ArtifactReducerOutput)
    dependency: DependencyReducerOutput = Field(default_factory=DependencyReducerOutput)
    library: LibraryReducerOutput = Field(default_factory=LibraryReducerOutput)
    claim: ClaimReducerOutput = Field(default_factory=ClaimReducerOutput)
    state_hash: str = ""
    reducer_registry_hash: str = ""
    prefix_time: str = "1970-01-01T00:00:00Z"


class ConformanceExpectedResult(LoscrModel):
    status: CheckerStatus
    supported_level: ClaimLevel
    failure_family: FailureFamily | None = None
    failure_code: str | None = None


class ConformanceFixture(LoscrModel):
    fixture_id: str
    description: str = ""
    contract: ClaimContract
    context: dict[str, Any] = Field(default_factory=dict)
    expected: ConformanceExpectedResult
