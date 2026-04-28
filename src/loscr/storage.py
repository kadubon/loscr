"""Append-only JSONL storage for local LOSCR ledgers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, TypeVar

from pydantic import BaseModel, ValidationError

from loscr.hashing import attach_integrity_hash, canonical_hash, canonical_json
from loscr.ledgers import canonical_ledger_name
from loscr.models import (
    AdapterContract,
    BaselineRegistryEntry,
    BoundaryCertificate,
    CheckerResult,
    ClaimContract,
    DelayedLabelRecord,
    DependencyGraph,
    EdgeEventEnvelope,
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
    ReinvestmentLedgerEdge,
    RejectionRecord,
    ReplayRecord,
    ResourceLedgerEvent,
    SequentialMonitoringProfile,
    ServiceCapacityEnvelope,
    ServiceLedgerEvent,
    ServiceLoadContract,
    ServiceObligation,
    TrustedBaseEntry,
    WipItemEvent,
)


T = TypeVar("T", bound=BaseModel)

LEDGER_MODELS: dict[str, type[BaseModel]] = {
    "edge_events": EdgeEventEnvelope,
    "adapter_contracts": AdapterContract,
    "service_ledger": ServiceLedgerEvent,
    "service_obligations": ServiceObligation,
    "service_load_contracts": ServiceLoadContract,
    "service_capacity_envelopes": ServiceCapacityEnvelope,
    "resource_ledger": ResourceLedgerEvent,
    "delayed_label_ledger": DelayedLabelRecord,
    "claim_contracts": ClaimContract,
    "epoch_bridges": EpochBridge,
    "checker_results": CheckerResult,
    "gate_ledger": GateLedgerEvent,
    "wip_ledger": WipItemEvent,
    "exploration_ledger": ExplorationBudgetEvent,
    "baseline_registry": BaselineRegistryEntry,
    "evaluator_health": EvaluatorHealth,
    "estimator_profiles": EstimatorProfile,
    "sequential_profiles": SequentialMonitoringProfile,
    "dependency_graphs": DependencyGraph,
    "incidents": IncidentNode,
    "frontier_governance": FrontierGovernanceContract,
    "frontier_sampling_frames": FrontierSamplingFrame,
    "replay_records": ReplayRecord,
    "trusted_base_registry": TrustedBaseEntry,
    "library_entries": LibraryEntry,
    "promotion_attribution": PromotionAttributionRecord,
    "reinvestment_edges": ReinvestmentLedgerEdge,
    "boundary_certificates": BoundaryCertificate,
    "rejections": RejectionRecord,
}


class JsonlLedgerStore:
    """Local append-only JSONL ledger store.

    The public append APIs never delete or rewrite ledger files. Reducer snapshots
    are cached separately under ``.loscr/snapshots`` and can always be rebuilt.
    """

    def __init__(self, root: str | Path = ".loscr") -> None:
        self.root = Path(root)
        self.ledgers_dir = self.root / "ledgers"
        self.snapshots_dir = self.root / "snapshots"

    def init(self) -> None:
        self.ledgers_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        (self.root / "profiles").mkdir(parents=True, exist_ok=True)

    def ledger_path(self, ledger: str) -> Path:
        ledger = canonical_ledger_name(ledger)
        if "/" in ledger or "\\" in ledger or ledger in {"", ".", ".."}:
            raise ValueError(f"invalid ledger name: {ledger!r}")
        return self.ledgers_dir / f"{ledger}.jsonl"

    def append(self, ledger: str, record: BaseModel | dict[str, Any]) -> BaseModel:
        """Validate and append one record to a ledger.

        Schema-invalid records are represented as replay-inert rejection records.
        Integrity failures remain in their source ledger so reducers can quarantine
        affected scopes.
        """
        self.init()
        ledger = canonical_ledger_name(ledger)
        model_type = LEDGER_MODELS.get(ledger)
        try:
            model = self._coerce_record(model_type, record)
        except ValidationError as exc:
            rejection = self._append_rejection(ledger, record, str(exc))
            return rejection
        self._append_model(ledger, model)
        return model

    def append_many(
        self, ledger: str, records: Iterable[BaseModel | dict[str, Any]]
    ) -> tuple[int, int]:
        accepted = 0
        rejected = 0
        for record in records:
            appended = self.append(ledger, record)
            if isinstance(appended, RejectionRecord):
                rejected += 1
            else:
                accepted += 1
        return accepted, rejected

    def read_raw(self, ledger: str) -> list[dict[str, Any]]:
        ledger = canonical_ledger_name(ledger)
        path = self.ledger_path(ledger)
        if not path.exists():
            return []
        records: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as handle:
            for index, line in enumerate(handle):
                stripped = line.strip()
                if not stripped:
                    continue
                data = json.loads(stripped)
                if isinstance(data, dict):
                    data["_append_index"] = index
                    records.append(data)
        return records

    def read_models(self, ledger: str, model_type: type[T]) -> list[T]:
        models: list[T] = []
        for record in self.read_raw(ledger):
            record.pop("_append_index", None)
            models.append(model_type.model_validate(record))
        return models

    def write_snapshot(self, name: str, snapshot: BaseModel | dict[str, Any]) -> Path:
        self.init()
        path = self.snapshots_dir / f"{name}.json"
        path.write_text(canonical_json(snapshot) + "\n", encoding="utf-8")
        return path

    def read_snapshot(self, name: str) -> dict[str, Any] | None:
        path = self.snapshots_dir / f"{name}.json"
        if not path.exists():
            return None
        loaded = json.loads(path.read_text(encoding="utf-8"))
        return loaded if isinstance(loaded, dict) else None

    def ledger_names(self) -> list[str]:
        if not self.ledgers_dir.exists():
            return []
        return sorted(path.stem for path in self.ledgers_dir.glob("*.jsonl"))

    def _coerce_record(
        self, model_type: type[BaseModel] | None, record: BaseModel | dict[str, Any]
    ) -> BaseModel:
        if isinstance(record, BaseModel):
            if model_type is not None and not isinstance(record, model_type):
                return model_type.model_validate(record.model_dump(mode="json"))
            return record
        if model_type is None:
            return _GenericLedgerRecord.model_validate(record)
        return model_type.model_validate(record)

    def _append_model(self, ledger: str, model: BaseModel) -> None:
        path = self.ledger_path(ledger)
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(canonical_json(model) + "\n")

    def _append_rejection(
        self, ledger: str, record: BaseModel | dict[str, Any], reason: str
    ) -> RejectionRecord:
        raw = record.model_dump(mode="json") if isinstance(record, BaseModel) else record
        rejection_data: dict[str, Any] = {
            "rejection_id": canonical_hash({"ledger": ledger, "record": raw, "reason": reason}),
            "source_ledger": ledger,
            "reason": reason,
            "raw_record_hash": canonical_hash(raw),
            "created_at": "1970-01-01T00:00:00Z",
            "replay_inert": True,
        }
        rejection = RejectionRecord.model_validate(attach_integrity_hash(rejection_data))
        self._append_model("rejections", rejection)
        return rejection


class _GenericLedgerRecord(BaseModel):
    model_config = {"extra": "allow"}
