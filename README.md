# LOSCR

Layered Online Service and Certified Replay Control.

LOSCR is a local-first Python reference implementation for converting
AI-assisted R&D work into replayable, machine-checkable claim evidence. It gives
engineers and coding agents a small set of deterministic building blocks:
append-only JSONL ledgers, canonical JSON hashing, pure reducers, service
accounting, replay/library records, dependency incident reachability, and a
conservative claim checker.

The practical use case is simple: before a team says that an AI R&D workflow is
observable, controlled, audited, production-ready, causal, transferable,
frontier-grade, or reinvestment-positive, LOSCR checks whether the local evidence
actually supports that claim. Unsupported strong claims are downgraded,
invalidated, or quarantined with machine-readable failure codes.

Keywords: AI R&D verification, AI agent evidence, local-first evidence ledger,
machine-checkable claims, deterministic replay, JSONL ledger, claim checker,
service control, evaluator audit, baseline contamination, dependency graph,
incident reachability, certified replay.

## Why This Exists

AI-generated work is not verified progress until validation, replay, evaluator
health, baseline integrity, service capacity, dependency safety, and maintenance
burden are charged. LOSCR makes those conditions explicit and checkable instead
of relying on dashboards, anecdotes, or informal agent self-assessment.

## Start Here

```bash
uv sync
uv run loscr demo quickstart
uv run loscr doctor
uv run loscr conformance run examples/synthetic_conformance
```

For the smallest Layer 0 observable example:

```bash
uv run loscr init
uv run loscr ingest jsonl examples/layer0_minimal/edge_events.jsonl --ledger edge_events
uv run loscr reduce
uv run loscr check --claim examples/layer0_minimal/claim_contract.yaml --append-result
uv run loscr reduce
uv run loscr report
```

For the bundled controlled daily example:

```bash
uv run loscr init
uv run loscr ingest jsonl examples/daily_minimal/edge_events.jsonl --ledger edge_events
uv run loscr ingest jsonl examples/daily_minimal/gate_ledger.jsonl --ledger gate_ledger
uv run loscr ingest jsonl examples/daily_minimal/wip_ledger.jsonl --ledger wip_ledger
uv run loscr ingest jsonl examples/daily_minimal/service_ledger.jsonl --ledger service_ledger
uv run loscr ingest jsonl examples/daily_minimal/service_obligations.jsonl --ledger service_obligations
uv run loscr reduce
uv run loscr check --claim examples/daily_minimal/claim_contract.yaml --append-result
uv run loscr reduce
uv run loscr report
```

`loscr doctor` initializes a local `.loscr/` store when needed. Runtime defaults
are local-only and network-free.

## Choose Your Adoption Level

| Level | Add | Use when |
| --- | --- | --- |
| 0 | Layer 0 edge ledgers | You need observable local work evidence. |
| 1 | Gate and WIP reducers | You need controlled local operation and hard-stop visibility. |
| 2 | Service obligations and envelopes | You need service-controlled claims and queue capacity evidence. |
| 3 | Evaluator, baseline, dependency checks | You need audited or production-operational claims. |
| 4 | Replay and library records | You need certified reusable artifacts. |
| 5 | Causal, transfer, frontier, reinvestment evidence | You need strong claims with estimator, bridge, governance, or lineage evidence. |

## Common Outcomes

| Status | Meaning | Safe response |
| --- | --- | --- |
| `valid` | Current evidence supports the requested claim level. | Keep the result with its hashes and ledger prefix. |
| `downgraded` | Evidence supports only a weaker level. | Use `supported_level`, repair evidence, or lower the claim. |
| `invalid` | Required identifiers or schema cannot support the claim. | Fix source records or report descriptive evidence only. |
| `quarantined` | Integrity, incident, evaluator, hard-stop, replay, or trusted-base evidence blocks positive credit. | Quarantine/narrow scope, repair evidence, and recheck. |

## Documentation Map

- Quick demo: [docs/quick-demo.md](docs/quick-demo.md)
- Layer 0 quickstart: [docs/layer0-quickstart.md](docs/layer0-quickstart.md)
- Failure-code cookbook: [docs/failure-code-cookbook.md](docs/failure-code-cookbook.md)
- GitHub Actions: [docs/github-actions.md](docs/github-actions.md)
- Theory map: [docs/theory-map.md](docs/theory-map.md)
- Operations and adoption policies: [docs/operations.md](docs/operations.md)
- Repository metadata: [docs/repository-metadata.md](docs/repository-metadata.md)

## What LOSCR Does

- Stores local evidence as inspectable append-only JSONL ledgers under
  `.loscr/ledgers/`.
- Hashes records with deterministic canonical JSON and SHA-256 integrity hashes.
- Rebuilds state snapshots from ledger prefixes with deterministic reducers.
- Accounts for Layer 0 telemetry, Layer 1 service obligations, and Layer 2
  replay/library promotion state.
- Checks claim contracts against canonical profiles and a failure-code transition
  matrix.
- Fails closed: missing identifiers are invalid; corrupted replay, revoked
  trusted bases, hard stops, and incident-reachable claims quarantine affected
  scope; missing production evidence downgrades to the strongest supported level.
- Exports JSON Schemas so other agents and tools can generate compatible records.
- Runs without network calls by default and does not require API keys.

## What It Is Not

LOSCR is not a dashboard, benchmark score, semantic judge, LLM evaluator, or
remote service. It does not decide whether research is "important" or "good".
It checks whether explicit evidence supports explicit claims under deterministic
rules.

LOSCR includes deterministic reference statistical primitives for logged
propensity estimation, doubly robust finite-window totals, audit lower bounds,
time-uniform lower confidence values, epsilon dominance, rate-improvement
margins, and finite-horizon reinvestment lower bounds. It is still not a full
statistical consulting package: specialized estimators and causal designs remain
modular extension points, but their outputs should be sealed into typed LOSCR
records and consumed by the fail-closed checker.

## Install And Quickstart

LOSCR uses Python 3.12+ and `uv`.

```bash
uv sync
uv run loscr --help
uv run loscr demo quickstart
```

Run the minimal local example:

```bash
uv run loscr init
uv run loscr ingest jsonl examples/daily_minimal/edge_events.jsonl --ledger edge_events
uv run loscr ingest jsonl examples/daily_minimal/gate_ledger.jsonl --ledger gate_ledger
uv run loscr ingest jsonl examples/daily_minimal/wip_ledger.jsonl --ledger wip_ledger
uv run loscr ingest jsonl examples/daily_minimal/service_ledger.jsonl --ledger service_ledger
uv run loscr ingest jsonl examples/daily_minimal/service_obligations.jsonl --ledger service_obligations
uv run loscr reduce
uv run loscr check --claim examples/daily_minimal/claim_contract.yaml --append-result
uv run loscr reduce
uv run loscr report
```

Seal a YAML or JSON record before ingestion or sharing:

```bash
uv run loscr seal examples/daily_minimal/claim_contract.yaml --model ClaimContract --out claim.sealed.json
```

Export machine-readable schemas:

```bash
uv run loscr schema export --out schemas/
```

## Organization Decisions

LOSCR makes evidence checkable, but each organization must predeclare the local
policy choices that define what the evidence means. These decisions should be
recorded before using LOSCR for production, causal, transfer, frontier, or
reinvestment claims. `uv run loscr init` writes a local `.loscr/config.yaml`
template with these decision areas.

- Scope and ownership: claim scopes, owners, station names, task strata,
  supported claim levels, and when contracts must be sealed.
- Adapter policy: source systems, field maps, stable identifiers, timestamp
  rules, privacy filters, and the strongest claim level each adapter can
  support.
- Raw content policy: whether any raw prompts, diffs, traces, artifacts, or
  reviewer notes may be stored; the default should be hashes and protected trace
  hashes.
- Service policy: validation, audit, replay, maintenance, and registry service
  channels; service units; load contracts; reservation rules; queue-age
  envelopes; overload actions; and recalibration cadence.
- Evaluator policy: evaluator floors by claim level, sentinel pools, canary
  budgets, known-good/known-bad sources, leakage probes, audit cadence, and
  revocation triggers.
- Baseline policy: frozen, rolling, shadow, or external baselines; assignment
  rules; bridge designs; contamination tests; update cadence; and baseline-debt
  ceilings.
- Dependency and incident policy: graph boundaries, unknown-dependency budgets,
  boundary certificates, hard-stop classes, incident reachability rules, and
  closure criteria.
- Estimator and monitoring policy: assignment logs, positivity floors, outcome
  caps, missingness rules, interference handling, uncertainty rules, sequential
  alpha, freeze triggers, and diagnostic pass/fail thresholds.
- Frontier policy: source admission authority, quotas, weights, blinding,
  deduplication, leakage screens, minimum task mass, dispute rules, and update
  cadence.
- Library and reinvestment policy: trusted-base governance, replay tiers,
  signature rules, maintenance due times, promotion evidence, negative-lineage
  audits, cohort dilution, and retirement rules.
- Security and release policy: local secret scanning, signing or approval,
  retention, access control, private vulnerability reporting, and release review.

These policies can be stricter than LOSCR defaults. They should not weaken the
fail-closed behavior for strong claims.

## Architecture

Layer 0, edge telemetry:
`EdgeEventEnvelope` records factual work events, resource use, parent links,
input/output hashes, substrate fingerprints, queue age, dependency flags, and
claim scope. `telemetry_reducer` verifies integrity, checks parent links,
computes coverage, and detects substrate drift without bridge evidence.

Layer 1, service control:
`ServiceLedgerEvent`, `ServiceObligation`, and `ServiceLoadContract` account for
required, reserved, completed, cancelled, expired, and held service quantities.
`service_reducer` computes queue state, overloads, and suspect or quarantined
service contracts. Service-controlled or stronger claims require declared
`service_envelopes` and active or recalibrated service load contracts; missing
load contracts fail closed to controlled. `resource_reducer`, `delayed_label_reducer`,
`pressure_reducer`, and `artifact_reducer` cover resource-vector accounting,
logged delayed labels, bottleneck pressure, and ordinary artifact health without
requiring a dashboard or external service.

Estimator and monitoring primitives:
`loscr.stats` implements the paper's local deterministic math surfaces:
Horvitz-Thompson totals, doubly robust totals, audit-debt lower bounds,
conservative lower confidence values, epsilon dominance, scalar
rate-improvement margins, and finite-horizon reinvestment lower bounds. These
functions are pure helpers for producing sealed diagnostics; the checker still
requires explicit `EstimatorProfile`, delayed-label, sequential-monitoring, and
lineage records before supporting strong claims.

Layer 2, certified replay library:
`ReplayRecord`, `TrustedBaseEntry`, `LibraryEntry`,
`PromotionAttributionRecord`, and `ReinvestmentLedgerEdge` represent reusable
evidence. `library_reducer` quarantines entries under revoked trusted bases,
marks expired maintenance, and distinguishes candidate, admitted, promoted, due,
quarantined, and retired entries.

Checker:
`loscr.checker.check(contract, state, registries)` is pure and deterministic for
a fixed ledger prefix, reducer registry, and trusted-base registry. The result
contains `check_id`, supported level, supported claim form, failure codes,
violated fields, required actions, frozen intervals, dependency hash, state hash,
checker version hash, and integrity hash.

## Claim Levels

LOSCR claim levels are ordered:

```text
descriptive
observable
controlled
service_controlled
audited
production_operational
production_causal
transfer
frontier
reinvestment
```

Examples:

- `observable`: Layer 0 telemetry coverage is sufficient.
- `controlled`: gate and WIP ledgers make hard stops and unresolved work visible.
- `service_controlled`: service reservations and queue-age envelopes are valid.
- `audited`: evaluator state is monitored or stronger.
- `production_operational`: audited evaluator, baseline, dependency graph, and
  hard-constraint evidence are present.
- `production_causal`: causal design fields and estimator profile pass.
- `transfer`: a target epoch bridge supports target strata, substrate/service,
  and evaluator comparability.
- `frontier`: sealed source, sampling frame, quota, weights, deduplication,
  blinding, leakage screen, minimum task mass, and governance contract are
  present.
- `reinvestment`: promoted library entries, signed lineage, negative lineage
  audit, bounded attribution, and finite-horizon lower bound are present.

## CLI Reference

```bash
uv run loscr init [PATH]
uv run loscr seal FILE --model ModelName --out sealed.json
uv run loscr schema export --out schemas/
uv run loscr ingest jsonl FILE --ledger edge_events
uv run loscr reduce
uv run loscr check --claim claim.yaml
uv run loscr check --claim claim.yaml --append-result
uv run loscr check --claim claim.yaml --format markdown
uv run loscr replay
uv run loscr report
uv run loscr report --format json
uv run loscr doctor
uv run loscr audit-public
uv run loscr conformance run examples/synthetic_conformance
```

`check` is read-only by default. Use `--append-result` when the checker result
should become part of the `checker_results` ledger. `reduce` writes a replayable
state snapshot under `.loscr/snapshots/`. JSONL ledgers remain the source of
truth. `replay` rebuilds state from ledgers and checks whether the stored
snapshot hash still matches.

## Python API

```python
from pathlib import Path

from loscr.checker import CheckerRegistries, check
from loscr.models import ClaimContract
from loscr.state import build_snapshot, context_from_store
from loscr.storage import JsonlLedgerStore

store = JsonlLedgerStore(Path(".loscr"))
snapshot = build_snapshot(store)
context = context_from_store(store, snapshot)

contract = ClaimContract.model_validate_json(Path("claim.sealed.json").read_text())
result = check(contract, context, CheckerRegistries())

print(result.status.value, result.supported_level.value)
print([f"{code.family.value}.{code.code}" for code in result.failure_codes])
```

To seal records programmatically:

```python
from loscr.model_registry import seal_record

sealed = seal_record("ClaimContract", {"claim_id": "claim", "...": "..."})
```

Use the deterministic statistical helpers to produce auditable estimator
diagnostics:

```python
from loscr.models import LoggedPropensityObservation
from loscr.stats import horvitz_thompson_total, time_uniform_lower_confidence_bound

estimate = horvitz_thompson_total(
    [
        LoggedPropensityObservation(
            observation_id="obs-1",
            assignment_probability=0.5,
            value=10.0,
        )
    ],
    positivity_floor=0.1,
)
lower = time_uniform_lower_confidence_bound(
    cumulative_sum=estimate.estimate_total,
    variance_upper_bound=estimate.variance_upper_bound or 0.0,
)
print(estimate.output_hash, lower.lower_bound)
```

## Extension Points

Adapters:
Implement local adapters that read operational artifacts and emit Pydantic LOSCR
models. Existing adapters cover generic JSONL, local git metadata, JUnit XML,
and local LLM/tool logs. Adapters should hash private content by default and
must not require network access.

Reducers:
Add pure reducer functions that take explicit records and return deterministic
Pydantic outputs with an `output_hash`. Reducers must be replayable from a
ledger prefix and must not read hidden global state.

Checker rules:
Add profile or transition rules only when the required evidence is explicitly
represented by schemas, ledgers, dependency graphs, or registries. Do not encode
informal semantic judgment as checker logic.

Schemas:
Run `uv run loscr schema export --out schemas/` and publish the generated JSON
Schemas when building tools or agents that produce LOSCR records.

Operations:
See `docs/operations.md` for a deployment checklist and the local policy
decisions that should be versioned before relying on strong claims.

## Operational Notes

- Runtime defaults are local-only and network-free.
- Public storage APIs append only. Corrections are new records that point to the
  corrected record.
- Malformed ingested records become replay-inert rejection records.
- `uv run loscr audit-public` scans public text files for high-confidence
  secrets and personal local machine paths before release.
- Determinism assumes a fixed ledger prefix, reducer registry, checker version,
  canonical profile registry, and trusted-base registry.
- Store raw private content outside LOSCR ledgers unless a local policy
  explicitly allows it. Prefer input/output hashes and protected trace hashes.

## Conformance And Development

```bash
uv run ruff check
uv run mypy src
uv run pytest
uv run loscr conformance run examples/synthetic_conformance
```

Synthetic conformance fixtures cover missing identifiers, stale evaluators,
service overload, baseline contamination, corrupted replay, and hard-stop
dependency reachability.

## Repository Layout

```text
src/loscr/              Python package and CLI
src/loscr/checker/      deterministic claim checker
src/loscr/reducers/     pure reducer implementations
src/loscr/adapters/     local adapter modules
src/loscr/schemas/      JSON Schema export
examples/               daily and synthetic conformance examples
tests/                  unit and conformance tests
docs/                   theory map and implementation details
```

## Citation

See `CITATION.cff`.

Takahashi, K. (2026). *Layered Online Service and Replay Control for Verified AI
R and D Acceleration*. Zenodo. https://doi.org/10.5281/zenodo.19836225

## License

Apache License 2.0. SPDX-License-Identifier: Apache-2.0.
