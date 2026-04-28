"""Public model registry for tools that need dynamic schema/model lookup."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from loscr.integrity import seal_model
from loscr.models import (
    AdapterContract,
    AuditBoundInput,
    AuditBoundResult,
    ArtifactReducerOutput,
    BaselineRegistryEntry,
    BaselineReducerOutput,
    BaselineUpdateContract,
    BoundaryCertificate,
    CheckerResult,
    ClaimContract,
    ClaimLevelProfile,
    ClaimReducerOutput,
    ConformanceFixture,
    DelayedLabelRecord,
    DelayedLabelReducerOutput,
    DependencyEdge,
    DependencyGraph,
    DependencyNode,
    DependencyReducerOutput,
    EdgeEventEnvelope,
    EdgeEventSidecar,
    EpochBridge,
    EpsilonDominanceInput,
    EpsilonDominanceResult,
    EstimatorProfile,
    EstimatorResult,
    EvaluatorAuditProfile,
    EvaluatorHealth,
    ExplorationBudgetEvent,
    ExplorationReducerOutput,
    FieldStatusRecord,
    ConfidenceSequenceResult,
    FiniteHorizonReinvestmentInput,
    FiniteHorizonReinvestmentResult,
    FrontierGovernanceContract,
    FrontierSamplingFrame,
    GateLedgerEvent,
    GateReducerOutput,
    IncidentNode,
    LibraryEntry,
    LibraryReducerOutput,
    LoggedPropensityObservation,
    PromotionAttributionRecord,
    RateImprovementResult,
    ReducerIssue,
    ReducerSnapshot,
    RejectionRecord,
    ReinvestmentLedgerEdge,
    ReplayRecord,
    ResourceLedgerEvent,
    ResourceRaw,
    ResourceReducerOutput,
    SequentialMonitoringProfile,
    ServiceCapacityEnvelope,
    ServiceChannel,
    ServiceLedgerEvent,
    ServiceLoadContract,
    ServiceObligation,
    ServiceQueueState,
    ServiceReducerOutput,
    PressureReducerOutput,
    TelemetryReducerOutput,
    TrustedBaseEntry,
    TrustedBaseRegistry,
    WipItemEvent,
    WipReducerOutput,
)


MODEL_REGISTRY: dict[str, type[BaseModel]] = {
    model.__name__: model
    for model in (
        AdapterContract,
        AuditBoundInput,
        AuditBoundResult,
        ResourceRaw,
        ResourceLedgerEvent,
        ResourceReducerOutput,
        EdgeEventEnvelope,
        FieldStatusRecord,
        EdgeEventSidecar,
        LoggedPropensityObservation,
        ClaimLevelProfile,
        ClaimContract,
        ClaimReducerOutput,
        CheckerResult,
        EpochBridge,
        ServiceChannel,
        ServiceLedgerEvent,
        ServiceObligation,
        ServiceLoadContract,
        ServiceCapacityEnvelope,
        ServiceQueueState,
        ServiceReducerOutput,
        ReplayRecord,
        TrustedBaseEntry,
        TrustedBaseRegistry,
        LibraryEntry,
        LibraryReducerOutput,
        PromotionAttributionRecord,
        ReinvestmentLedgerEdge,
        EvaluatorAuditProfile,
        EvaluatorHealth,
        BaselineRegistryEntry,
        BaselineReducerOutput,
        BaselineUpdateContract,
        FrontierGovernanceContract,
        FrontierSamplingFrame,
        EstimatorProfile,
        EstimatorResult,
        SequentialMonitoringProfile,
        ConfidenceSequenceResult,
        EpsilonDominanceInput,
        EpsilonDominanceResult,
        RateImprovementResult,
        FiniteHorizonReinvestmentInput,
        FiniteHorizonReinvestmentResult,
        DelayedLabelRecord,
        DelayedLabelReducerOutput,
        DependencyGraph,
        DependencyNode,
        DependencyEdge,
        DependencyReducerOutput,
        BoundaryCertificate,
        IncidentNode,
        GateLedgerEvent,
        GateReducerOutput,
        WipItemEvent,
        WipReducerOutput,
        ExplorationBudgetEvent,
        ExplorationReducerOutput,
        TelemetryReducerOutput,
        PressureReducerOutput,
        ArtifactReducerOutput,
        RejectionRecord,
        ReducerIssue,
        ReducerSnapshot,
        ConformanceFixture,
    )
}


def model_names() -> list[str]:
    """Return registered public model names."""
    return sorted(MODEL_REGISTRY)


def get_model(name: str) -> type[BaseModel]:
    """Return a registered model by class name."""
    try:
        return MODEL_REGISTRY[name]
    except KeyError as exc:
        raise KeyError(f"unknown LOSCR model: {name}") from exc


def seal_record(model_name: str, data: dict[str, Any]) -> BaseModel:
    """Validate a mapping as a named model and recompute its integrity hash."""
    model_type = get_model(model_name)
    if "integrity_hash" in model_type.model_fields and "integrity_hash" not in data:
        data = {**data, "integrity_hash": ""}
    model = model_type.model_validate(data)
    return seal_model(model)
