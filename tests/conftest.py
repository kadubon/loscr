from __future__ import annotations

from typing import Any

import pytest

from loscr.hashing import attach_integrity_hash, compute_integrity_hash
from loscr.models import (
    BaselineRegistryEntry,
    ClaimContract,
    EdgeEventEnvelope,
    EvaluatorHealth,
    ResourceRaw,
)


def _make_event(**overrides: Any) -> EdgeEventEnvelope:
    data: dict[str, Any] = {
        "event_id": "evt-1",
        "event_type": "work",
        "timestamp": "2026-01-01T00:00:00Z",
        "item_id": "item-1",
        "parent_event_id": None,
        "station_id": "dev",
        "policy_id": "policy",
        "action_type": "edit",
        "substrate_fingerprint": "substrate-1",
        "status_raw": "completed",
        "resource_raw": ResourceRaw(wall_time=1.0).model_dump(mode="json"),
        "queue_channel": "dev",
        "queue_age_raw": 0.0,
        "dependency_flag": False,
        "reuse_count": 0,
        "input_hash": "sha256:input",
        "output_hash": "sha256:output",
        "claim_scope_id": "scope",
    }
    data.update(overrides)
    return EdgeEventEnvelope.model_validate(attach_integrity_hash(data))


def _make_contract(**overrides: Any) -> ClaimContract:
    data: dict[str, Any] = {
        "claim_id": "claim",
        "contract_epoch": "epoch-1",
        "claim_level": "controlled",
        "claim_form": "operational",
        "scope": "scope",
        "station_set": ["dev"],
        "task_strata": ["work"],
        "ledger_schema_ids": ["edge_events"],
        "freeze_rule": "exclude_frozen",
        "downgrade_rule": "canonical",
        "escalation_rule": "checker_only",
        "hard_constraints": ["security"],
    }
    data.update(overrides)
    model = ClaimContract.model_validate({**data, "integrity_hash": ""})
    return model.model_copy(update={"integrity_hash": compute_integrity_hash(model)})


def _make_evaluator(**overrides: Any) -> EvaluatorHealth:
    data: dict[str, Any] = {
        "evaluator_id": "eval",
        "state": "audited",
        "known_good_pass_lcb": 0.99,
        "known_bad_reject_lcb": 0.99,
        "canary_integrity": True,
        "shortcut_probe_failure_ucb": 0.0,
        "leakage_signal": False,
        "blinded_review_disagreement_ucb": 0.0,
        "missingness": 0.0,
        "audit_age_windows": 0,
    }
    data.update(overrides)
    return EvaluatorHealth.model_validate(data)


def _make_baseline(**overrides: Any) -> BaselineRegistryEntry:
    data: dict[str, Any] = {
        "baseline_id": "base",
        "baseline_type": "shadow",
        "policy_identity": "baseline-policy",
        "substrate_fingerprint": "substrate-1",
        "contamination_test": True,
        "bridge_status": "none",
        "contaminated": False,
        "baseline_debt": 0.0,
    }
    data.update(overrides)
    return BaselineRegistryEntry.model_validate(data)


@pytest.fixture
def make_event() -> Any:
    return _make_event


@pytest.fixture
def make_contract() -> Any:
    return _make_contract


@pytest.fixture
def make_evaluator() -> Any:
    return _make_evaluator


@pytest.fixture
def make_baseline() -> Any:
    return _make_baseline
