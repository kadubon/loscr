"""Reducer extension registry.

The registry is metadata-first: it lets tools discover reducer names, versions,
input ledgers, output models, and a deterministic registry hash without forcing
all reducers into a single call signature.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from pydantic import BaseModel

from loscr.hashing import canonical_hash
from loscr.models import (
    ArtifactReducerOutput,
    BaselineReducerOutput,
    ClaimReducerOutput,
    DelayedLabelReducerOutput,
    DependencyReducerOutput,
    ExplorationReducerOutput,
    GateReducerOutput,
    LibraryReducerOutput,
    PressureReducerOutput,
    ResourceReducerOutput,
    ServiceReducerOutput,
    TelemetryReducerOutput,
    WipReducerOutput,
)
from loscr.reducers.artifact import artifact_reducer
from loscr.reducers.baseline import baseline_reducer
from loscr.reducers.claim import claim_reducer
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


@dataclass(frozen=True)
class ReducerSpec:
    name: str
    version: str
    input_ledgers: tuple[str, ...]
    output_model: type[BaseModel]
    reducer: Callable[..., BaseModel]

    def metadata(self) -> dict[str, object]:
        """Return deterministic registry metadata without the Python callable."""
        return {
            "name": self.name,
            "version": self.version,
            "input_ledgers": list(self.input_ledgers),
            "output_model": self.output_model.__name__,
        }


class ReducerRegistry:
    """Explicit reducer registry for agents and applications."""

    def __init__(self) -> None:
        self._reducers: dict[str, ReducerSpec] = {}

    def register(self, spec: ReducerSpec) -> None:
        if spec.name in self._reducers:
            raise ValueError(f"reducer already registered: {spec.name}")
        self._reducers[spec.name] = spec

    def get(self, name: str) -> ReducerSpec:
        try:
            return self._reducers[name]
        except KeyError as exc:
            raise KeyError(f"unknown reducer: {name}") from exc

    def list_names(self) -> list[str]:
        return sorted(self._reducers)

    def metadata(self) -> list[dict[str, object]]:
        return [self._reducers[name].metadata() for name in self.list_names()]

    def registry_hash(self) -> str:
        return canonical_hash(self.metadata())

    def hash(self) -> str:
        """Backward-compatible alias for ``registry_hash``."""
        return self.registry_hash()


def default_reducer_registry() -> ReducerRegistry:
    """Return the built-in reducer registry."""
    registry = ReducerRegistry()
    for spec in (
        ReducerSpec(
            "telemetry",
            "v1",
            ("edge_events",),
            TelemetryReducerOutput,
            telemetry_reducer,
        ),
        ReducerSpec(
            "service",
            "v1",
            ("service_ledger", "service_obligations", "service_load_contracts"),
            ServiceReducerOutput,
            service_reducer,
        ),
        ReducerSpec(
            "claim",
            "v1",
            ("claim_contracts", "checker_results"),
            ClaimReducerOutput,
            claim_reducer,
        ),
        ReducerSpec(
            "dependency",
            "v1",
            ("dependency_graphs", "incidents"),
            DependencyReducerOutput,
            dependency_reducer,
        ),
        ReducerSpec(
            "library",
            "v1",
            ("replay_records", "trusted_base_registry", "library_entries"),
            LibraryReducerOutput,
            library_reducer,
        ),
        ReducerSpec("baseline", "v1", ("baseline_registry",), BaselineReducerOutput, baseline_reducer),
        ReducerSpec("gate", "v1", ("gate_ledger", "incidents"), GateReducerOutput, gate_reducer),
        ReducerSpec("wip", "v1", ("wip_ledger",), WipReducerOutput, wip_reducer),
        ReducerSpec(
            "resource",
            "v1",
            ("edge_events", "resource_ledger"),
            ResourceReducerOutput,
            resource_reducer,
        ),
        ReducerSpec(
            "delayed_label",
            "v1",
            ("delayed_label_ledger",),
            DelayedLabelReducerOutput,
            delayed_label_reducer,
        ),
        ReducerSpec(
            "pressure",
            "v1",
            ("wip_reducer", "service_reducer"),
            PressureReducerOutput,
            pressure_reducer,
        ),
        ReducerSpec(
            "artifact",
            "v1",
            ("edge_events",),
            ArtifactReducerOutput,
            artifact_reducer,
        ),
        ReducerSpec(
            "exploration",
            "v1",
            ("exploration_ledger", "incidents"),
            ExplorationReducerOutput,
            exploration_reducer,
        ),
    ):
        registry.register(spec)
    return registry
