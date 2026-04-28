"""Ledger naming and alias helpers.

The paper uses conceptual names such as ``edge_log`` and ``dependency_graph``.
The reference implementation stores JSONL files with stable pluralized names.
These helpers keep checker/profile logic independent from file naming details.
"""

from __future__ import annotations


LEDGER_ALIASES: dict[str, str] = {
    "edge_log": "edge_events",
    "edge_events": "edge_events",
    "adapter_contracts": "adapter_contracts",
    "service_ledger": "service_ledger",
    "service_obligation_ledger": "service_obligations",
    "service_obligations": "service_obligations",
    "load_contract_ledger": "service_load_contracts",
    "service_load_contracts": "service_load_contracts",
    "service_capacity_envelope_ledger": "service_capacity_envelopes",
    "service_capacity_envelopes": "service_capacity_envelopes",
    "resource_ledger": "resource_ledger",
    "resource_events": "resource_ledger",
    "claim_contract_ledger": "claim_contracts",
    "claim_contracts": "claim_contracts",
    "epoch_bridge_ledger": "epoch_bridges",
    "epoch_bridges": "epoch_bridges",
    "checker_result_ledger": "checker_results",
    "checker_results": "checker_results",
    "gate_ledger": "gate_ledger",
    "wip_ledger": "wip_ledger",
    "exploration_ledger": "exploration_ledger",
    "baseline_registry": "baseline_registry",
    "dependency_graph": "dependency_graphs",
    "dependency_graphs": "dependency_graphs",
    "hard_constraint_ledger": "incidents",
    "incident_ledger": "incidents",
    "incidents": "incidents",
    "audit_ledger": "evaluator_health",
    "evaluator_health": "evaluator_health",
    "delayed_label_ledger": "delayed_label_ledger",
    "delayed_labels": "delayed_label_ledger",
    "estimator_profile_ledger": "estimator_profiles",
    "estimator_profiles": "estimator_profiles",
    "sequential_monitoring_ledger": "sequential_profiles",
    "sequential_profiles": "sequential_profiles",
    "frontier_governance": "frontier_governance",
    "frontier_sampling_frames": "frontier_sampling_frames",
    "replay_record_ledger": "replay_records",
    "replay_records": "replay_records",
    "trusted_base_registry": "trusted_base_registry",
    "library_entries": "library_entries",
    "boundary_certificates": "boundary_certificates",
    "promotion_attribution": "promotion_attribution",
    "reinvestment_edges": "reinvestment_edges",
    "rejections": "rejections",
}


def canonical_ledger_name(name: str) -> str:
    """Return the storage ledger name for a theory or implementation ledger name."""
    return LEDGER_ALIASES.get(name, name)


def normalize_ledger_names(names: list[str] | set[str] | tuple[str, ...]) -> set[str]:
    """Normalize a collection of ledger names for profile comparisons."""
    return {canonical_ledger_name(name) for name in names}
