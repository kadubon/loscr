"""State composition helpers for library users and the CLI."""

from __future__ import annotations

from loscr.checker import CheckerContext
from loscr.models import (
    BaselineRegistryEntry,
    CheckerResult,
    ClaimContract,
    DelayedLabelRecord,
    DependencyGraph,
    EpochBridge,
    EstimatorProfile,
    EvaluatorHealth,
    ExplorationBudgetEvent,
    FrontierGovernanceContract,
    FrontierSamplingFrame,
    GateLedgerEvent,
    IncidentNode,
    LibraryEntry,
    PromotionAttributionRecord,
    ReducerSnapshot,
    ReinvestmentLedgerEdge,
    ReplayRecord,
    ResourceLedgerEvent,
    SequentialMonitoringProfile,
    ServiceLedgerEvent,
    ServiceLoadContract,
    ServiceObligation,
    TrustedBaseEntry,
    WipItemEvent,
)
from loscr.reducers.baseline import baseline_reducer
from loscr.reducers.claim import claim_reducer
from loscr.reducers.control_state import finalize_snapshot
from loscr.reducers.artifact import artifact_reducer
from loscr.reducers.delayed_label import delayed_label_reducer
from loscr.reducers.dependency import dependency_reducer
from loscr.reducers.exploration import exploration_reducer
from loscr.reducers.gate import gate_reducer
from loscr.reducers.library import library_reducer
from loscr.reducers.pressure import pressure_reducer
from loscr.reducers.resource import resource_reducer
from loscr.reducers.service import service_reducer
from loscr.reducers.telemetry import telemetry_reducer
from loscr.reducers.wip import wip_reducer
from loscr.storage import JsonlLedgerStore


def build_snapshot(store: JsonlLedgerStore) -> ReducerSnapshot:
    """Build a deterministic reducer snapshot from append-only ledgers."""
    edge_events = store.read_raw("edge_events")
    telemetry = telemetry_reducer(edge_events)
    incidents = store.read_models("incidents", IncidentNode)
    gate = gate_reducer(store.read_models("gate_ledger", GateLedgerEvent), incidents)
    wip = wip_reducer(store.read_models("wip_ledger", WipItemEvent))
    service = service_reducer(
        store.read_models("service_ledger", ServiceLedgerEvent),
        store.read_models("service_obligations", ServiceObligation),
        store.read_models("service_load_contracts", ServiceLoadContract),
        control_time=telemetry.latest_event_time,
    )
    baseline = baseline_reducer(store.read_models("baseline_registry", BaselineRegistryEntry))
    exploration = exploration_reducer(
        store.read_models("exploration_ledger", ExplorationBudgetEvent), incidents
    )
    resource = resource_reducer(
        edge_events,
        store.read_models("resource_ledger", ResourceLedgerEvent),
    )
    delayed_label = delayed_label_reducer(
        store.read_models("delayed_label_ledger", DelayedLabelRecord)
    )
    contracts = store.read_models("claim_contracts", ClaimContract)
    results = store.read_models("checker_results", CheckerResult)
    dependency_graphs = store.read_models("dependency_graphs", DependencyGraph)
    dependency = dependency_reducer(dependency_graphs[-1] if dependency_graphs else None, incidents)
    library = library_reducer(
        store.read_models("replay_records", ReplayRecord),
        store.read_models("trusted_base_registry", TrustedBaseEntry),
        [
            *store.read_models("promotion_attribution", PromotionAttributionRecord),
            *store.read_models("reinvestment_edges", ReinvestmentLedgerEdge),
        ],
        store.read_models("library_entries", LibraryEntry),
        control_time=telemetry.latest_event_time or "9999-12-31T00:00:00Z",
    )
    claim_state = claim_reducer(contracts, results, incidents)
    pressure = pressure_reducer(wip, service)
    artifact = artifact_reducer(edge_events)
    snapshot = ReducerSnapshot(
        telemetry=telemetry,
        gate=gate,
        wip=wip,
        service=service,
        baseline=baseline,
        exploration=exploration,
        resource=resource,
        delayed_label=delayed_label,
        pressure=pressure,
        artifact=artifact,
        dependency=dependency,
        library=library,
        claim=claim_state,
        prefix_time=telemetry.latest_event_time or "1970-01-01T00:00:00Z",
    )
    return finalize_snapshot(snapshot)


def context_from_store(store: JsonlLedgerStore, snapshot: ReducerSnapshot) -> CheckerContext:
    """Create a checker context from a store and reducer snapshot."""
    evaluator_health = {
        item.evaluator_id: item for item in store.read_models("evaluator_health", EvaluatorHealth)
    }
    baseline_registry = {
        item.baseline_id: item for item in store.read_models("baseline_registry", BaselineRegistryEntry)
    }
    frontier_governance = {
        item.source_id: item
        for item in store.read_models("frontier_governance", FrontierGovernanceContract)
    }
    frontier_sampling = {
        item.source_id: item
        for item in store.read_models("frontier_sampling_frames", FrontierSamplingFrame)
    }
    epoch_bridges = {
        item.bridge_id: item for item in store.read_models("epoch_bridges", EpochBridge)
    }
    estimator_profiles = {
        item.estimator_id: item
        for item in store.read_models("estimator_profiles", EstimatorProfile)
    }
    sequential_profiles = {
        item.claim_id: item
        for item in store.read_models("sequential_profiles", SequentialMonitoringProfile)
    }
    trusted_base_entries = {
        item.trusted_base_id: item
        for item in store.read_models("trusted_base_registry", TrustedBaseEntry)
    }
    return CheckerContext(
        telemetry=snapshot.telemetry,
        service=snapshot.service,
        resource=snapshot.resource,
        delayed_label=snapshot.delayed_label,
        dependency=snapshot.dependency,
        library=snapshot.library,
        snapshot=snapshot,
        ledgers_present=store.ledger_names(),
        evaluator_health=evaluator_health,
        baseline_registry=baseline_registry,
        frontier_governance=frontier_governance,
        frontier_sampling_frames=frontier_sampling,
        epoch_bridges=epoch_bridges,
        estimator_profiles=estimator_profiles,
        sequential_profiles=sequential_profiles,
        trusted_base_entries=trusted_base_entries,
        promotion_attribution=store.read_models(
            "promotion_attribution", PromotionAttributionRecord
        ),
        reinvestment_edges=store.read_models("reinvestment_edges", ReinvestmentLedgerEdge),
        hard_stop_claim_ids=snapshot.gate.hard_stop_claim_ids,
        frozen_intervals=snapshot.exploration.frozen_claims,
        instrumentation_burden_exceeded=bool(snapshot.resource.uncharged_burden_scopes),
        state_hash=snapshot.state_hash,
        dependency_hash=snapshot.dependency.output_hash,
        prefix_time=snapshot.prefix_time,
    )
