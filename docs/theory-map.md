# Theory Map

Layer 0 is implemented by `EdgeEventEnvelope`, `EdgeEventSidecar`, the JSONL
`edge_events` ledger, `telemetry_reducer`, and the lightweight `gate_reducer`
and `wip_reducer` used by the daily profile.

Layer activation follows the paper's conservative ladder. Ordinary work can
start with Layer 0. Layer 1 evidence becomes material when service queues have
positive age, a claim is production-level or stronger, an output is reused by
downstream items, an action is external-facing, evaluator/safety/replay/
maintenance/registry dependencies are present, a baseline/frontier/ledger claim
is made, or Layer 0 missingness exceeds tolerance. Layer 2 is activated only
when an artifact is claimed as certified reusable capital or supports certified
library or reinvestment claims.

Layer 1 is implemented by service channels, service obligations,
`ServiceLedgerEvent`, `ServiceLoadContract`, `service_reducer`,
`resource_reducer`, `delayed_label_reducer`, `pressure_reducer`, and the
`exploration_reducer` for bounded exposure accounting.
Service-controlled and stronger claims require explicit service envelopes plus
active or recalibrated load contracts. Missing load contracts, broken service
hashes, held/expired obligations, or overloaded queues cap support at
controlled.

Layer 2 is implemented by replay records, trusted-base entries, library entries,
promotion attribution records, reinvestment ledger edges, and `library_reducer`.
The checker treats revoked, stale, or out-of-scope trusted-base entries as
integrity failures for relevant production claims.

Ordinary artifact state is represented by `artifact_reducer`, which provides the
paper's lightweight `artifact_reducer(edge_events, dependency_graph)` extension
surface without turning artifact value into an informal semantic judgment.

The paper's mathematical estimator surfaces are implemented in `loscr.stats` as
pure deterministic functions: Horvitz-Thompson finite-window totals, doubly
robust finite-window totals, audit-debt lower bounds, conservative lower
confidence values, epsilon dominance, rate-improvement margins, and
finite-horizon reinvestment lower bounds. These functions deliberately produce
typed, hashed diagnostics rather than bypassing the checker.

The deterministic checker is `loscr.checker.core.check`. It follows the
reference order: schema, integrity, epoch, replay reconstruction, incident scope,
hard constraints, telemetry coverage, claim profile, claim form, service,
evaluator, baseline/frontier, dependency, estimator, burden, and final supported
level.

Append-only ledgers live under `.loscr/ledgers/`. Reducer snapshots are
rebuildable caches under `.loscr/snapshots/`; JSONL remains source of truth.
`loscr.ledgers` maps paper names such as `edge_log` and `dependency_graph` to
the JSONL storage names used by the reference implementation.

Failure-code transitions are encoded in `transitions.py`. Quarantine dominates
downgrade, and missing identifiers are invalid. Transfer, frontier,
reinvestment, estimator, and freeze failures are represented as explicit failure
codes rather than informal interpretation:

- transfer requires a valid `EpochBridge` for the target epoch;
- frontier requires governance and sampling-frame evidence;
- frontier governance must include sealed source status, pre-outcome weights,
  blinding, leakage screening, deduplication, and sufficient sampling mass;
- causal and reinvestment claims require an admissible `EstimatorProfile`;
- reinvestment requires promoted entries, bounded attribution, signed lineage,
  negative lineage audit, and finite-horizon lower-bound edges;
- frozen intervals require a sealed sequential monitoring profile.

Dependency graphs and incident reachability determine affected claim scope. A
hard stop, corrupted replay, revoked trusted base, or unresolved incident in
scope blocks positive strong credit until repaired.
