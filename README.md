# LOSCR

Which level of claim is supported by recorded workflow evidence? **Layered Online
Service and Certified Replay Control (LOSCR)** checks AI-assisted R&D claims against
declared profiles and local append-only ledgers. Missing or conflicting evidence can
downgrade, invalidate or quarantine a claim rather than silently support a stronger one.

Current source and [GitHub release](https://github.com/kadubon/loscr/releases/tag/v0.1.0):
**0.1.0**, Python 3.12+, Apache-2.0. The orientation below uses a source checkout;
no LOSCR PyPI publication is asserted. Profile acceptance is not independent proof
of production causality or deployment readiness. Suitable external statistical and
causal designs remain necessary.

## Why This Exists

AI-generated work is not verified progress until validation, replay, evaluator
health, baseline integrity, service capacity, dependency safety, and maintenance
burden are charged. LOSCR makes those conditions explicit and checkable instead
of relying on dashboards, anecdotes, or informal agent self-assessment.

## Start Here

Use one disposable source checkout. From its root, prepare the environment (POSIX
shell or PowerShell); `uv sync` may access the network:

```sh
uv sync
uv run loscr --help
```

After setup, the optional smallest demo writes temporary synthetic ledgers, removes
them afterward, and prints claim outcomes. It does not create a project `.loscr/`
store or access a model/network:

```sh
uv run loscr demo quickstart --format json
```

Inspect `status`, `supported_level` and `failure_codes`; the scenarios illustrate
valid, downgraded and quarantined claims under fixed profiles, not real-world judgments.
Commands here are source-checked, not newly execution-verified.

For persistent state, **both `init` and `doctor` can initialize `.loscr/`**.
Use a fresh disposable checkout/directory before following the
[Layer 0 ledger path](docs/layer0-quickstart.md) or
[controlled daily example](examples/daily_minimal/README.md).
Ingestion appends records; reduction writes snapshots; `check --append-result`
adds checker evidence. Do not mistake those paths for read-only inspection.

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

These statuses are relative to the declared claim/profile, ledger prefix and trusted
registries. They are not unconditional judgments of external truth or action safety.

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

Use the single [Start Here](#start-here) path above. The [quick demo](docs/quick-demo.md)
and [Layer 0 guide](docs/layer0-quickstart.md) explain required fixture paths and output.
Repository-relative `examples/` files require the checkout; they are not assumed to
appear in an arbitrary installed working directory. An unprepared `uv run` may resolve
dependencies before running a local command.

## Organization Decisions

Predeclare scope, ownership, adapters/privacy, service units, evaluator policy,
baselines, dependencies/incidents, estimators, frontier governance, replay/library
and security policy before relying on stronger claims. The existing
[operations guide](docs/operations.md) retains the detailed policy inventory.
`init` writes a `.loscr/config.yaml` template, not proof that those policies are adequate.

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

The [CLI source](src/loscr/cli.py) defines actual commands and flags. The
[quick-demo guide](docs/quick-demo.md) explains inputs and results without duplicating
a command catalogue here. `check` is read-only by default; `--append-result` writes
the result ledger. `reduce` writes snapshots under `.loscr/snapshots/`, and `replay`
also writes the rebuilt snapshot after comparison. `doctor` can initialize missing
state. Use a fresh store for writing examples; ledgers remain the source of truth.

## Machine-readable interfaces

- [Record models and ClaimContract](src/loscr/models.py),
  [model registry/sealing](src/loscr/model_registry.py), and
  [claim result](src/loscr/checker/result.py).
- [Claim checker](src/loscr/checker/core.py) and
  [failure-code cookbook](docs/failure-code-cookbook.md).
- [Layer 0 claim fixture](examples/layer0_minimal/claim_contract.yaml) and
  [negative conformance fixtures](examples/synthetic_conformance/).
- Schema export is `uv run loscr schema export --out schemas/` from a prepared
  checkout; it writes files, so choose a fresh destination. See [schema exporter](src/loscr/schemas/).

## Python API

With LOSCR installed, the following inspection requires an existing initialized
`.loscr/` store and an actual `claim.sealed.json` in the current directory. It reads
those inputs and computes a result; it is not a standalone initialization example.

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

Partial API sketch only: supply a complete real ClaimContract before sealing; the ellipsis field below is not valid evidence:

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
See [operations](docs/operations.md) for a deployment checklist and the local policy
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

Software release:

Takahashi, K. (2026). *LOSCR: Layered Online Service and Certified Replay
Control (v0.1.0)*. Zenodo. https://doi.org/10.5281/zenodo.19875498

Associated paper:

Takahashi, K. (2026). *Layered Online Service and Replay Control for Verified AI
R and D Acceleration*. Zenodo. https://doi.org/10.5281/zenodo.19836225

## License

Apache License 2.0. SPDX-License-Identifier: Apache-2.0.

## Research navigation

The [Collective Intelligence Research and OSS Index](https://kadubon.github.io/github.io/collective-intelligence-index.html)
connects [production reliability](https://kadubon.github.io/github.io/collective-intelligence-index.html#problem-production-reliability)
and [evaluation integrity](https://kadubon.github.io/github.io/collective-intelligence-index.html#problem-evaluation-integrity)
to the necessary evidence and external responsibilities. It does not certify a deployment.
