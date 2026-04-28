"""Machine-readable conformance fixture runner."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from loscr.checker import CheckerContext, CheckerRegistries, check
from loscr.models import (
    BaselineRegistryEntry,
    ConformanceFixture,
    DelayedLabelReducerOutput,
    DependencyReducerOutput,
    EvaluatorHealth,
    LibraryReducerOutput,
    ServiceReducerOutput,
    ResourceReducerOutput,
    TelemetryReducerOutput,
)


def load_conformance_fixture(path: str | Path) -> ConformanceFixture:
    """Load a conformance fixture from YAML or JSON."""
    fixture_path = Path(path)
    raw_text = fixture_path.read_text(encoding="utf-8")
    loaded: Any
    if fixture_path.suffix.lower() == ".json":
        loaded = json.loads(raw_text)
    else:
        loaded = yaml.safe_load(raw_text)
    if not isinstance(loaded, dict):
        raise ValueError("conformance fixture must be a mapping")
    return ConformanceFixture.model_validate(loaded)


def context_from_fixture(fixture: ConformanceFixture) -> CheckerContext:
    """Build a checker context from a compact fixture dictionary."""
    raw = fixture.context
    evaluator_health = {
        item["evaluator_id"]: EvaluatorHealth.model_validate(item)
        for item in raw.get("evaluator_health", [])
    }
    baseline_registry = {
        item["baseline_id"]: BaselineRegistryEntry.model_validate(item)
        for item in raw.get("baseline_registry", [])
    }
    return CheckerContext(
        telemetry=TelemetryReducerOutput.model_validate(raw.get("telemetry", {})),
        service=ServiceReducerOutput.model_validate(raw.get("service", {})),
        resource=ResourceReducerOutput.model_validate(raw.get("resource", {})),
        delayed_label=DelayedLabelReducerOutput.model_validate(raw.get("delayed_label", {})),
        dependency=DependencyReducerOutput.model_validate(raw.get("dependency", {})),
        library=LibraryReducerOutput.model_validate(raw.get("library", {})),
        ledgers_present=list(raw.get("ledgers_present", [])),
        evaluator_health=evaluator_health,
        baseline_registry=baseline_registry,
        hard_stop_claim_ids=list(raw.get("hard_stop_claim_ids", [])),
        frozen_intervals=list(raw.get("frozen_intervals", [])),
        replay_corrupted=bool(raw.get("replay_corrupted", False)),
        unbridged_epoch_change=bool(raw.get("unbridged_epoch_change", False)),
        instrumentation_burden_exceeded=bool(
            raw.get("instrumentation_burden_exceeded", False)
        ),
        state_hash=raw.get("state_hash"),
        dependency_hash=raw.get("dependency_hash"),
        prefix_time=str(raw.get("prefix_time", "1970-01-01T00:00:00Z")),
    )


def run_conformance_fixture(path: str | Path) -> tuple[bool, dict[str, Any]]:
    """Run one conformance fixture and return pass/fail plus machine-readable details."""
    fixture = load_conformance_fixture(path)
    result = check(fixture.contract, context_from_fixture(fixture), CheckerRegistries())
    expected = fixture.expected
    failure_pairs = {(item.family, item.code) for item in result.failure_codes}
    expected_failure_ok = True
    if expected.failure_family is not None:
        expected_failure_ok = (expected.failure_family, expected.failure_code or "") in failure_pairs
    passed = (
        result.status == expected.status
        and result.supported_level == expected.supported_level
        and expected_failure_ok
    )
    return passed, {
        "fixture_id": fixture.fixture_id,
        "passed": passed,
        "expected": expected.model_dump(mode="json"),
        "actual": {
            "status": result.status.value,
            "supported_level": result.supported_level.value,
            "failure_codes": [
                {"family": item.family.value, "code": item.code}
                for item in result.failure_codes
            ],
        },
    }


def run_conformance_path(path: str | Path) -> list[dict[str, Any]]:
    """Run one fixture file or all fixture YAML/JSON files below a directory."""
    target = Path(path)
    files = (
        [target]
        if target.is_file()
        else sorted(
            item
            for item in target.rglob("*")
            if item.name in {"fixture.yaml", "fixture.yml", "fixture.json"}
        )
    )
    return [run_conformance_fixture(item)[1] for item in files]
