from __future__ import annotations

import json
from pathlib import Path

import yaml
from typer.testing import CliRunner

from loscr.cli import app


def test_cli_smoke(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    runner = CliRunner()
    examples_dir = Path(__file__).resolve().parents[1] / "examples"
    fixture_dir = str(examples_dir / "synthetic_conformance")
    layer0_dir = examples_dir / "layer0_minimal"
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert Path(".loscr/profiles/canonical_profiles.json").exists()
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    config = yaml.safe_load(Path(".loscr/config.yaml").read_text(encoding="utf-8"))
    assert "organization_decisions" in config
    assert "service_policy" in config["organization_decisions"]
    result = runner.invoke(app, ["schema", "export", "--out", "schemas"])
    assert result.exit_code == 0
    result = runner.invoke(app, ["conformance", "run", fixture_dir])
    assert result.exit_code == 0
    result = runner.invoke(app, ["demo", "quickstart", "--format", "json"])
    assert result.exit_code == 0
    demo = json.loads(result.stdout)
    statuses = {item["status"] for item in demo["cases"]}
    assert {"valid", "downgraded", "quarantined"}.issubset(statuses)
    result = runner.invoke(
        app,
        ["ingest", "jsonl", str(layer0_dir / "edge_events.jsonl"), "--ledger", "edge_events"],
    )
    assert result.exit_code == 0
    result = runner.invoke(app, ["reduce"])
    assert result.exit_code == 0
    result = runner.invoke(
        app,
        ["check", "--claim", str(layer0_dir / "claim_contract.yaml"), "--append-result"],
    )
    assert result.exit_code == 0
    check_result = json.loads(result.stdout)
    assert check_result["status"] == "valid"
    assert check_result["supported_level"] == "observable"
    result = runner.invoke(app, ["reduce"])
    assert result.exit_code == 0
    result = runner.invoke(app, ["report", "--format", "json"])
    assert result.exit_code == 0
    report = json.loads(result.stdout)
    assert report["supported_claims"]["layer0-observable-claim"] == "observable"
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
