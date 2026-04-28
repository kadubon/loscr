"""Dependency graph and incident reachability reducer."""

from __future__ import annotations

from collections.abc import Sequence

import networkx as nx

from loscr.hashing import canonical_hash
from loscr.models import (
    BoundaryCertificate,
    DependencyEdge,
    DependencyGraph,
    DependencyNode,
    DependencyReducerOutput,
    IncidentNode,
)


def dependency_reducer(
    dependency_graph: DependencyGraph | dict[str, object] | None,
    incidents: Sequence[IncidentNode | dict[str, object]],
) -> DependencyReducerOutput:
    """Compute incident reachability and dependency coverage."""
    graph = (
        DependencyGraph(graph_id="empty")
        if dependency_graph is None
        else dependency_graph
        if isinstance(dependency_graph, DependencyGraph)
        else DependencyGraph.model_validate(dependency_graph)
    )
    parsed_incidents = [
        item if isinstance(item, IncidentNode) else IncidentNode.model_validate(item)
        for item in incidents
    ]
    nx_graph = nx.DiGraph()
    nodes_by_id: dict[str, DependencyNode] = {node.node_id: node for node in graph.nodes}
    for node in graph.nodes:
        nx_graph.add_node(node.node_id)
    for edge in graph.edges:
        nx_graph.add_edge(edge.source, edge.target, edge_type=edge.edge_type, known=edge.known)

    claim_node_ids = [node.node_id for node in graph.nodes if node.node_type == "claim"]
    incident_reachable_claims: dict[str, list[str]] = {}
    for incident in parsed_incidents:
        reachable: list[str] = []
        if incident.node_id in nx_graph:
            descendants = nx.descendants(nx_graph, incident.node_id)
            for claim_id in claim_node_ids:
                claim_node = nodes_by_id.get(claim_id)
                if claim_id in descendants or (
                    incident.affected_scope
                    and claim_node is not None
                    and claim_node.claim_scope_id == incident.affected_scope
                ):
                    reachable.append(claim_id)
        incident_reachable_claims[incident.incident_id] = sorted(set(reachable))

    unknown_by_claim: dict[str, int] = {claim_id: 0 for claim_id in claim_node_ids}
    total_by_claim: dict[str, int] = {claim_id: 0 for claim_id in claim_node_ids}
    for edge in graph.edges:
        affected_claims = _reachable_claims_from_edge_target(nx_graph, edge.target, claim_node_ids)
        for claim_id in affected_claims:
            total_by_claim[claim_id] += 1
            if not edge.known:
                unknown_by_claim[claim_id] += 1

    expanded_boundaries = [
        cert.boundary_id for cert in graph.boundary_certificates if not cert.valid or cert.stale
    ]
    dependency_coverage_by_claim: dict[str, float] = {}
    unknown_fraction_by_claim: dict[str, float] = {}
    for claim_id in claim_node_ids:
        total = total_by_claim.get(claim_id, 0)
        unknown = unknown_by_claim.get(claim_id, 0)
        dependency_coverage_by_claim[claim_id] = 1.0 if total == 0 else (total - unknown) / total
        unknown_fraction_by_claim[claim_id] = 0.0 if total == 0 else unknown / total

    output = DependencyReducerOutput(
        incident_reachable_claims=incident_reachable_claims,
        dependency_coverage_by_claim=dependency_coverage_by_claim,
        unknown_dependency_fraction_by_claim=unknown_fraction_by_claim,
        expanded_boundaries=sorted(expanded_boundaries),
    )
    return output.model_copy(update={"output_hash": canonical_hash(output)})


def _reachable_claims_from_edge_target(
    graph: nx.DiGraph, target: str, claim_node_ids: list[str]
) -> list[str]:
    if target not in graph:
        return []
    descendants = nx.descendants(graph, target)
    descendants.add(target)
    return [claim_id for claim_id in claim_node_ids if claim_id in descendants]


__all__ = [
    "BoundaryCertificate",
    "DependencyEdge",
    "DependencyGraph",
    "DependencyNode",
    "dependency_reducer",
]
