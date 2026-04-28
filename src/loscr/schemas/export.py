"""Export JSON Schemas for public LOSCR data models."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, TypeAdapter

from loscr import enums
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
    ConformanceExpectedResult,
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
    FailureCode,
    FieldStatusRecord,
    FrontierGovernanceContract,
    FrontierSamplingFrame,
    ConfidenceSequenceResult,
    FiniteHorizonReinvestmentInput,
    FiniteHorizonReinvestmentResult,
    GateLedgerEvent,
    GateReducerOutput,
    IncidentNode,
    LibraryEntry,
    LibraryReducerOutput,
    LoggedPropensityObservation,
    PromotionAttributionRecord,
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
    RateImprovementResult,
    TelemetryReducerOutput,
    TrustedBaseEntry,
    TrustedBaseRegistry,
    WipItemEvent,
    WipReducerOutput,
)


MODEL_TYPES: tuple[type[BaseModel], ...] = (
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
    FailureCode,
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
    GateLedgerEvent,
    GateReducerOutput,
    WipItemEvent,
    WipReducerOutput,
    ExplorationBudgetEvent,
    ExplorationReducerOutput,
    TelemetryReducerOutput,
    PressureReducerOutput,
    ArtifactReducerOutput,
    DependencyGraph,
    DependencyNode,
    DependencyEdge,
    DependencyReducerOutput,
    BoundaryCertificate,
    IncidentNode,
    RejectionRecord,
    ReducerIssue,
    ReducerSnapshot,
    ConformanceExpectedResult,
    ConformanceFixture,
)

ENUM_TYPES: tuple[type[Enum], ...] = (
    enums.ClaimLevel,
    enums.ClaimForm,
    enums.CheckerStatus,
    enums.FailureFamily,
    enums.ServiceContractState,
    enums.ServiceObligationStatus,
    enums.EvaluatorState,
    enums.GateState,
    enums.ItemState,
    enums.FieldStatus,
    enums.ReplayTier,
    enums.TrustedBaseState,
    enums.LibraryState,
)


def export_json_schemas(out: str | Path) -> list[Path]:
    """Export JSON Schema files for all public model and enum schemas."""
    output_dir = Path(out)
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for model_type in MODEL_TYPES:
        path = output_dir / f"{model_type.__name__}.schema.json"
        path.write_text(_schema_json(model_type.model_json_schema()), encoding="utf-8")
        written.append(path)
    for enum_type in ENUM_TYPES:
        path = output_dir / f"{enum_type.__name__}.schema.json"
        path.write_text(_schema_json(TypeAdapter(enum_type).json_schema()), encoding="utf-8")
        written.append(path)
    return written


def _schema_json(schema: dict[str, Any]) -> str:
    import json

    return json.dumps(schema, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
