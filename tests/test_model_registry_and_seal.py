from __future__ import annotations

import yaml
from typer.testing import CliRunner

from loscr.adapters.contracts import default_adapter_contracts
from loscr.cli import app
from loscr.hashing import verify_integrity_hash
from loscr.model_registry import model_names, seal_record


def test_model_registry_seals_records() -> None:
    assert "ClaimContract" in model_names()
    sealed = seal_record(
        "ClaimContract",
        {
            "claim_id": "claim",
            "contract_epoch": "epoch-1",
            "claim_level": "controlled",
            "claim_form": "operational",
            "scope": "scope",
            "station_set": ["dev"],
            "task_strata": ["work"],
            "ledger_schema_ids": ["edge_events", "gate_ledger", "wip_ledger"],
            "freeze_rule": "exclude_frozen",
            "downgrade_rule": "canonical",
            "escalation_rule": "checker_only",
            "hard_constraints": ["security"],
        },
    )
    assert verify_integrity_hash(sealed)


def test_default_adapter_contracts_are_sealed() -> None:
    contracts = default_adapter_contracts()
    assert {"jsonl", "git", "junit", "llm_tool_log"} <= set(contracts)
    assert all(verify_integrity_hash(contract) for contract in contracts.values())


def test_cli_seal_command(tmp_path) -> None:  # type: ignore[no-untyped-def]
    input_path = tmp_path / "claim.yaml"
    output_path = tmp_path / "claim.sealed.json"
    input_path.write_text(
        yaml.safe_dump(
            {
                "claim_id": "claim",
                "contract_epoch": "epoch-1",
                "claim_level": "controlled",
                "claim_form": "operational",
                "scope": "scope",
                "station_set": ["dev"],
                "task_strata": ["work"],
                "ledger_schema_ids": ["edge_events", "gate_ledger", "wip_ledger"],
                "freeze_rule": "exclude_frozen",
                "downgrade_rule": "canonical",
                "escalation_rule": "checker_only",
                "hard_constraints": ["security"],
            }
        ),
        encoding="utf-8",
    )
    result = CliRunner().invoke(
        app, ["seal", str(input_path), "--model", "ClaimContract", "--out", str(output_path)]
    )
    assert result.exit_code == 0
    assert output_path.exists()
