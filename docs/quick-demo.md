# Quick Demo

LOSCR helps teams avoid treating AI-generated work as verified progress before
the evidence is present. It records local work as append-only JSONL ledgers,
rebuilds deterministic reducer state, and checks claim contracts against
explicit profiles. Strong claims are supported only when validation, replay,
evaluator health, baseline integrity, service capacity, dependency safety, and
maintenance burden are represented by evidence.

## What You Will See

- `loscr reduce` prints a deterministic `state_hash`.
- `loscr check` prints a `CheckerResult` with status, supported level, hashes,
  and failure codes.
- `loscr report` prints a compact local health summary.
- `loscr replay` rebuilds state and verifies the state hash matches.
- `loscr doctor` checks local store health.
- Synthetic conformance fixtures show downgrade, invalid, and quarantine paths.

## Minimal Daily Example

Run from the repository root:

```bash
uv sync
uv run loscr init
uv run loscr ingest jsonl examples/daily_minimal/edge_events.jsonl --ledger edge_events
uv run loscr ingest jsonl examples/daily_minimal/gate_ledger.jsonl --ledger gate_ledger
uv run loscr ingest jsonl examples/daily_minimal/wip_ledger.jsonl --ledger wip_ledger
uv run loscr ingest jsonl examples/daily_minimal/service_ledger.jsonl --ledger service_ledger
uv run loscr ingest jsonl examples/daily_minimal/service_obligations.jsonl --ledger service_obligations
uv run loscr reduce
uv run loscr check --claim examples/daily_minimal/claim_contract.yaml
uv run loscr replay
uv run loscr report
uv run loscr doctor
```

The daily example is intentionally small. It supports a controlled local claim,
not a production, causal, frontier, or reinvestment claim.

## Synthetic Conformance

Run:

```bash
uv run loscr conformance run examples/synthetic_conformance
```

The fixtures cover missing identifiers, stale evaluators, service overload,
baseline contamination, corrupted replay, and hard-stop dependency reachability.
They are safe for public CI because they use synthetic records only.

## Reading Command Output

### `loscr reduce`

Prints a state hash such as:

```text
sha256:...
```

The hash identifies the deterministic reducer snapshot for the current ledger
prefix.

### `loscr check`

Prints JSON by default. Important fields:

- `status`: `valid`, `downgraded`, `invalid`, or `quarantined`.
- `requested_level`: the claim level requested by the contract.
- `supported_level`: the strongest level supported by evidence.
- `failure_codes`: machine-readable reasons for downgrade, invalidation, or
  quarantine.
- `state_hash`, `dependency_hash`, `checker_version_hash`: reproducibility
  anchors.

### `loscr report`

Prints a compact human-readable summary: supported claims, missing identifiers,
hard stops, unresolved WIP, queue age, service overloads, baseline debt, and
active incidents.

### `loscr replay`

Rebuilds state from append-only ledgers. `replay ok` means the rebuilt state hash
matches the previous snapshot.

### `loscr doctor`

Checks store health. It should be run after `loscr init` in a new workspace.

## Downgrade

`downgraded` means LOSCR found evidence for a weaker claim, but not for the
requested stronger claim. This is useful: it tells users the strongest safe
claim level and the missing evidence to repair.

## Quarantine

`quarantined` means positive credit is blocked for the affected scope. Typical
causes include integrity failure, corrupted replay, incident reachability,
revoked trusted base, stale evaluator, or hard-stop reachability.

## Why Failure Is Useful

A failed, downgraded, invalid, or quarantined claim is not a generic tool
failure. It is evidence-control behavior. It prevents a workflow from turning
unsupported AI-assisted activity into an overstated claim.
