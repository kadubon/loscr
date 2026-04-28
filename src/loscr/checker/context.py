"""Checker input context models."""

from __future__ import annotations

from pydantic import Field

from loscr.models import (
    BaselineRegistryEntry,
    ClaimLevelProfile,
    DelayedLabelReducerOutput,
    EpochBridge,
    EstimatorProfile,
    EvaluatorHealth,
    FrontierGovernanceContract,
    FrontierSamplingFrame,
    LibraryReducerOutput,
    LoscrModel,
    PromotionAttributionRecord,
    ReducerSnapshot,
    ReinvestmentLedgerEdge,
    ResourceReducerOutput,
    SequentialMonitoringProfile,
    ServiceReducerOutput,
    TelemetryReducerOutput,
    TrustedBaseEntry,
    TrustedBaseRegistry,
)
from loscr.profiles import canonical_profiles
from loscr.transitions import DEFAULT_TRANSITIONS


class CheckerRegistries(LoscrModel):
    trusted_base_registry: TrustedBaseRegistry | None = None
    profiles: dict[str, ClaimLevelProfile] = Field(default_factory=canonical_profiles)
    transitions: dict[str, dict[str, str]] = Field(
        default_factory=lambda: {
            key.value: {
                "status": value.status.value,
                "max_supported_level": value.max_supported_level.value,
                "required_action": value.required_action,
            }
            for key, value in DEFAULT_TRANSITIONS.items()
        }
    )


class CheckerContext(LoscrModel):
    telemetry: TelemetryReducerOutput = Field(default_factory=TelemetryReducerOutput)
    service: ServiceReducerOutput = Field(default_factory=ServiceReducerOutput)
    resource: ResourceReducerOutput = Field(default_factory=ResourceReducerOutput)
    delayed_label: DelayedLabelReducerOutput = Field(default_factory=DelayedLabelReducerOutput)
    dependency: object | None = None
    library: LibraryReducerOutput = Field(default_factory=LibraryReducerOutput)
    snapshot: ReducerSnapshot | None = None
    ledgers_present: list[str] = Field(default_factory=list)
    evaluator_health: dict[str, EvaluatorHealth] = Field(default_factory=dict)
    baseline_registry: dict[str, BaselineRegistryEntry] = Field(default_factory=dict)
    frontier_governance: dict[str, FrontierGovernanceContract] = Field(default_factory=dict)
    frontier_sampling_frames: dict[str, FrontierSamplingFrame] = Field(default_factory=dict)
    epoch_bridges: dict[str, EpochBridge] = Field(default_factory=dict)
    estimator_profiles: dict[str, EstimatorProfile] = Field(default_factory=dict)
    sequential_profiles: dict[str, SequentialMonitoringProfile] = Field(default_factory=dict)
    trusted_base_entries: dict[str, TrustedBaseEntry] = Field(default_factory=dict)
    promotion_attribution: list[PromotionAttributionRecord] = Field(default_factory=list)
    reinvestment_edges: list[ReinvestmentLedgerEdge] = Field(default_factory=list)
    hard_stop_claim_ids: list[str] = Field(default_factory=list)
    frozen_intervals: list[str] = Field(default_factory=list)
    replay_corrupted: bool = False
    unbridged_epoch_change: bool = False
    instrumentation_burden_exceeded: bool = False
    state_hash: str | None = None
    dependency_hash: str | None = None
    prefix_time: str = "1970-01-01T00:00:00Z"
