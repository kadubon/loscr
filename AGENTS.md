# AGENTS.md

## What LOSCR Is

LOSCR is a local-first reference implementation of Layered Online Service and
Certified Replay Control. It turns AI-assisted R&D work into replayable,
machine-checkable evidence using append-only JSONL ledgers, canonical JSON
hashing, deterministic reducers, service accounting, dependency reachability,
replay/library records, and a conservative claim checker.

## When To Use LOSCR

- Use LOSCR when an agent needs to record or check evidence for an AI-assisted
  R&D claim.
- Use it when a workflow needs deterministic replay from local ledgers.
- Use it when a claim may need downgrade, invalidation, or quarantine instead
  of informal interpretation.
- Use it to test synthetic failure cases before trusting stronger claims.

## When Not To Use LOSCR

- Do not use LOSCR as a dashboard, benchmark leaderboard, LLM judge, or remote
  evaluator.
- Do not use it to decide whether research is important or valuable by
  semantic judgment.
- Do not use it to store raw private prompts, traces, code diffs, credentials,
  or local personal paths by default.
- Do not bypass failure codes to make a claim appear stronger.

## Fastest Safe Inspection

```bash
uv sync
uv run loscr --help
uv run loscr conformance run examples/synthetic_conformance
uv run pytest
```

For a local store:

```bash
uv run loscr init
uv run loscr doctor
```

## Checker Outcomes

- `valid`: the requested claim level is supported by the current evidence.
- `downgraded`: some evidence is missing or insufficient; use the supported
  lower level.
- `invalid`: required identifiers or schema cannot support a non-descriptive
  claim.
- `quarantined`: integrity, incident, evaluator, hard-stop, replay, or trusted
  base evidence blocks positive credit until repaired.

## Failure Codes

- Treat failure codes as evidence-control outputs, not generic tool errors.
- Do not suppress, reinterpret, or bypass them.
- Safe responses: repair evidence, add a bridge, rerun an audit, recalibrate a
  service contract, quarantine an artifact, narrow the scope, or lower the claim
  level.
- Unsafe responses: editing checker output, deleting ledger records, weakening
  profiles, or adding semantic judgment to make a strong claim pass.

## Safety Rules

- Runtime defaults must remain local-first and network-free.
- JSONL ledgers are append-only source of truth.
- Corrections are new records, not mutations.
- Reducers must be deterministic and pure over explicit inputs.
- Checker rules must be evidence-based and produce machine-readable failure
  codes.
- Prefer hashes and protected trace hashes over raw private content.
- Do not add telemetry, analytics, API keys, or remote calls.

## Inspect First

- `README.md`
- `docs/quick-demo.md`
- `docs/layer0-quickstart.md`
- `docs/failure-code-cookbook.md`
- `docs/theory-map.md`
- `docs/operations.md`
- `examples/`
- `src/loscr/checker/`
- `src/loscr/reducers/`
- `src/loscr/models.py`
- `tests/`

## Change Safely

- Add tests for schema, reducer, checker, CLI, or conformance behavior when
  changing behavior.
- Keep reducers pure and replayable from ledger prefixes.
- Keep checker logic tied to declared schemas, ledgers, profiles, dependency
  graphs, registries, and failure codes.
- Prefer explicit failure codes over informal judgment.
- Preserve fail-closed behavior for strong claims.

Before finishing, run:

```bash
uv run ruff check .
uv run mypy src
uv run pytest
uv run loscr conformance run examples/synthetic_conformance
```
