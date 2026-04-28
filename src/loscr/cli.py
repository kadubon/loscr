"""LOSCR command line interface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
import yaml
from rich.console import Console

from loscr.adapters.jsonl import read_jsonl_records
from loscr.checker import CheckerRegistries, check
from loscr.conformance import run_conformance_path
from loscr.hashing import canonical_json
from loscr.model_registry import model_names, seal_record
from loscr.models import (
    BaselineRegistryEntry,
    CheckerResult,
    ClaimContract,
    IncidentNode,
)
from loscr.profiles import canonical_profiles
from loscr.schemas import export_json_schemas
from loscr.security import scan_public_tree
from loscr.state import build_snapshot, context_from_store
from loscr.storage import JsonlLedgerStore

app = typer.Typer(no_args_is_help=True, help="LOSCR local-first reference implementation.")
schema_app = typer.Typer(help="JSON Schema commands.")
ingest_app = typer.Typer(help="Ingest local records.")
conformance_app = typer.Typer(help="Run machine-readable conformance fixtures.")
app.add_typer(schema_app, name="schema")
app.add_typer(ingest_app, name="ingest")
app.add_typer(conformance_app, name="conformance")
console = Console()


@app.command()
def init(path: Path = typer.Argument(Path("."), help="Repository or project path.")) -> None:
    """Create a local .loscr store."""
    root = path / ".loscr"
    store = JsonlLedgerStore(root)
    store.init()
    (root / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "project": "LOSCR",
                "storage": "jsonl",
                "network_runtime_default": "disabled",
                "organization_decisions": {
                    "scope_and_claim_policy": "define claim scopes, owners, claim levels, and seal timing",
                    "adapter_policy": "define source systems, field maps, identity rules, and privacy filters",
                    "raw_content_policy": "prefer hashes; explicitly approve any raw private content retention",
                    "service_policy": "define service channels, load contracts, reservations, and age envelopes",
                    "evaluator_policy": "define evaluator floors, sentinel audits, canaries, and revocation triggers",
                    "baseline_policy": "define shadow/frozen/external baselines, bridge rules, and debt ceilings",
                    "dependency_policy": "define graph boundaries, unknown-edge budgets, and incident reachability",
                    "estimator_policy": "define assignment logs, positivity floors, caps, missingness, and diagnostics",
                    "frontier_policy": "define admission, quotas, weights, blinding, deduplication, and leakage screens",
                    "library_policy": "define trusted bases, replay tiers, maintenance, lineage, and retirement",
                    "security_policy": "define secret scanning, signing, retention, access control, and release review",
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (root / "profiles" / "canonical_profiles.json").write_text(
        canonical_json(canonical_profiles()) + "\n",
        encoding="utf-8",
    )
    console.print(f"Initialized LOSCR store at {root}")


@schema_app.command("export")
def schema_export(out: Path = typer.Option(..., "--out", help="Output directory.")) -> None:
    """Export JSON Schemas for all public models."""
    written = export_json_schemas(out)
    console.print(f"Exported {len(written)} schemas to {out}")


@ingest_app.command("jsonl")
def ingest_jsonl(
    file: Path = typer.Argument(..., exists=True, readable=True),
    ledger: str = typer.Option(..., "--ledger", help="Ledger name, for example edge_events."),
) -> None:
    """Validate and append records from a local JSONL file."""
    store = JsonlLedgerStore()
    accepted, rejected = store.append_many(ledger, read_jsonl_records(file))
    console.print(f"Accepted {accepted}; rejected {rejected}; ledger={ledger}")
    if rejected:
        raise typer.Exit(code=1)


@app.command()
def seal(
    file: Path = typer.Argument(..., exists=True, readable=True),
    model: str = typer.Option(..., "--model", help="Registered LOSCR model class name."),
    out: Path | None = typer.Option(None, "--out", help="Output file. Defaults to stdout."),
) -> None:
    """Validate records and recompute deterministic integrity hashes."""
    if model not in set(model_names()):
        raise typer.BadParameter(f"unknown model {model}; known models: {', '.join(model_names())}")
    if file.suffix.lower() == ".jsonl":
        lines = []
        for line_number, line in enumerate(file.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            loaded = json.loads(stripped)
            if not isinstance(loaded, dict):
                raise typer.BadParameter(f"line {line_number} is not a JSON object")
            lines.append(canonical_json(seal_record(model, loaded)))
        payload = "\n".join(lines) + ("\n" if lines else "")
    else:
        loaded = yaml.safe_load(file.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise typer.BadParameter("input file must contain a mapping or JSONL objects")
        payload = canonical_json(seal_record(model, loaded)) + "\n"
    if out is None:
        console.print(payload, end="")
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload, encoding="utf-8")
        console.print(f"sealed {file} as {model} -> {out}")


@conformance_app.command("run")
def conformance_run(
    path: Path = typer.Argument(
        Path("examples/synthetic_conformance"),
        help="Fixture file or directory containing fixture.yaml files.",
    ),
) -> None:
    """Run synthetic conformance fixtures."""
    results = run_conformance_path(path)
    console.print_json(canonical_json(results))
    if any(not item["passed"] for item in results):
        raise typer.Exit(code=1)


@app.command()
def reduce() -> None:
    """Run deterministic reducers and write a local snapshot."""
    store = JsonlLedgerStore()
    snapshot = build_snapshot(store)
    store.write_snapshot("state", snapshot)
    console.print(snapshot.state_hash)


@app.command()
def replay() -> None:
    """Replay ledgers and compare the current state hash with the previous snapshot."""
    store = JsonlLedgerStore()
    previous = store.read_snapshot("state")
    snapshot = build_snapshot(store)
    store.write_snapshot("state", snapshot)
    previous_hash = previous.get("state_hash") if previous else None
    if previous_hash is None:
        console.print(f"state_hash={snapshot.state_hash}")
        return
    if previous_hash != snapshot.state_hash:
        console.print(f"replay mismatch previous={previous_hash} current={snapshot.state_hash}")
        raise typer.Exit(code=1)
    console.print(f"replay ok state_hash={snapshot.state_hash}")


def check_command(
    claim: Path = typer.Option(..., "--claim", exists=True, readable=True),
    output_format: str = typer.Option("json", "--format", help="json or markdown."),
    append_result: bool = typer.Option(
        False,
        "--append-result",
        help="Append the checker result to the checker_results ledger.",
    ),
) -> None:
    """Run the deterministic claim checker."""
    contract = ClaimContract.model_validate(_load_yaml_or_json(claim))
    store = JsonlLedgerStore()
    snapshot = build_snapshot(store)
    context = context_from_store(store, snapshot)
    result = check(contract, context, CheckerRegistries())
    if append_result:
        store.append("checker_results", result)
    if output_format == "markdown":
        _print_markdown_result(result)
    elif output_format == "json":
        console.print_json(canonical_json(result))
    else:
        raise typer.BadParameter("--format must be json or markdown")


app.command(name="check")(check_command)


@app.command()
def report(output_format: str = typer.Option("text", "--format", help="text or json.")) -> None:
    """Show a compact human-readable report for the current store."""
    store = JsonlLedgerStore()
    snapshot = build_snapshot(store)
    if output_format == "json":
        console.print_json(
            canonical_json(
                {
                    "state_hash": snapshot.state_hash,
                    "supported_claims": snapshot.claim.supported_levels,
                    "missing_identifier_events": snapshot.telemetry.missing_identifier_events,
                    "hard_stops": snapshot.gate.hard_stop_targets,
                    "unresolved_wip_by_scope": snapshot.wip.unresolved_wip_by_scope,
                    "max_queue_age_by_scope": snapshot.wip.max_queue_age_by_scope,
                    "service_overloads": snapshot.service.overloaded_queues,
                    "baseline_debt": snapshot.baseline.total_baseline_debt,
                    "active_incidents": _active_incident_ids(store),
                }
            )
        )
        return
    if output_format != "text":
        raise typer.BadParameter("--format must be text or json")
    service = snapshot.service
    oldest_queue_age = max((queue.oldest_age for queue in service.queue_states), default=0.0)
    console.print("[bold]LOSCR report[/bold]")
    console.print(f"state_hash: {snapshot.state_hash}")
    console.print(f"supported claims: {snapshot.claim.supported_levels}")
    console.print(f"missing identifier events: {snapshot.telemetry.missing_identifier_events}")
    console.print(f"hard stops: {snapshot.gate.hard_stop_targets}")
    console.print(f"unresolved WIP: {snapshot.wip.unresolved_wip_by_scope}")
    console.print(f"max WIP queue age: {snapshot.wip.max_queue_age_by_scope}")
    console.print(f"oldest queue age: {oldest_queue_age}")
    console.print(f"service overloads: {service.overloaded_queues}")
    console.print(f"quarantined contracts: {service.quarantined_contracts}")
    console.print(f"baseline debt: {snapshot.baseline.total_baseline_debt:.4f}")
    console.print(f"active incidents: {_active_incident_ids(store)}")


@app.command()
def doctor() -> None:
    """Validate local store health."""
    store = JsonlLedgerStore()
    store.init()
    problems: list[str] = []
    snapshot = build_snapshot(store)
    if not (store.root / "profiles" / "canonical_profiles.json").exists():
        problems.append("missing canonical profiles")
    if snapshot.telemetry.integrity_failures:
        problems.append(f"broken edge hashes: {snapshot.telemetry.integrity_failures}")
    if snapshot.library.quarantined_entries:
        problems.append(f"quarantined library entries: {snapshot.library.quarantined_entries}")
    previous = store.read_snapshot("state")
    if previous is not None and previous.get("state_hash") != snapshot.state_hash:
        problems.append("stored snapshot is not replayable from current ledger prefix")
    if problems:
        for problem in problems:
            console.print(f"[red]problem:[/red] {problem}")
        raise typer.Exit(code=1)
    console.print("doctor ok")


@app.command("audit-public")
def audit_public(path: Path = typer.Argument(Path("."), help="Repository path to scan.")) -> None:
    """Scan public files for high-confidence secrets and local machine paths."""
    findings = scan_public_tree(path)
    if findings:
        for item in findings:
            console.print(
                f"[red]{item.rule}[/red] {item.path}:{item.line} {item.excerpt}"
            )
        raise typer.Exit(code=1)
    console.print("public audit ok")


def _load_yaml_or_json(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise typer.BadParameter("claim file must contain a mapping")
    return data


def _print_markdown_result(result: CheckerResult) -> None:
    console.print("# LOSCR Check Result\n")
    console.print(f"- status: `{result.status.value}`")
    console.print(f"- requested_level: `{result.requested_level.value}`")
    console.print(f"- supported_level: `{result.supported_level.value}`")
    console.print(f"- state_hash: `{result.state_hash}`")
    if result.failure_codes:
        console.print("- failure_codes:")
        for item in result.failure_codes:
            console.print(f"  - `{item.family.value}.{item.code}`: {item.message}")


def _baseline_debt(store: JsonlLedgerStore) -> float:
    return sum(item.baseline_debt for item in store.read_models("baseline_registry", BaselineRegistryEntry))


def _active_incident_ids(store: JsonlLedgerStore) -> list[str]:
    return sorted(
        item.incident_id
        for item in store.read_models("incidents", IncidentNode)
        if item.resolved_at is None
    )


if __name__ == "__main__":
    app()
