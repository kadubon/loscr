from __future__ import annotations

from pathlib import Path

import yaml
from typer.testing import CliRunner

from loscr.cli import app


def test_cli_smoke(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    runner = CliRunner()
    fixture_dir = str(Path(__file__).resolve().parents[1] / "examples" / "synthetic_conformance")
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
    result = runner.invoke(app, ["reduce"])
    assert result.exit_code == 0
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
