# Checker

`check(contract, state, registries)` is pure and deterministic for a fixed
ledger prefix, reducer registry, and trusted-base registry. It returns a
`CheckerResult` containing failure codes, violated fields, required actions,
state hash, dependency hash, checker version hash, and integrity hash.

The checker does not make informal semantic judgments. Claim changes flow only
through canonical profiles, transition rules, dependency reachability, and
explicit state fields.

Strong-claim extension points are also fail-closed:

- `EpochBridge` records are required for transfer claims.
- `EstimatorProfile` records are required for causal and reinvestment claims.
  The reference checker requires assignment records, a positivity floor, an
  outcome cap, passing diagnostics, and additional no-leakage/residual-or-bound
  diagnostics for doubly robust profiles.
- `FrontierGovernanceContract` and `FrontierSamplingFrame` records are required
  for frontier claims. Governance must identify a sealed source, pre-outcome
  weights, blinding, leakage screening, deduplication, and a valid sampling
  mass.
- Active or recalibrated service load contracts are required for
  service-controlled and stronger claims.
- `PromotionAttributionRecord` and `ReinvestmentLedgerEdge` records are required
  for reinvestment claims.
- `SequentialMonitoringProfile` records are required when frozen intervals are
  present in production-or-stronger claims.

`loscr.stats` provides deterministic reference implementations for
Horvitz-Thompson totals, doubly robust totals, audit lower bounds, conservative
lower confidence values, epsilon dominance, rate-improvement margins, and
finite-horizon reinvestment lower bounds. Projects can use those helpers to
populate sealed estimator and lineage diagnostics. Richer local estimators may
be added, but the core checker should continue to consume only typed sealed
records and failure codes.

The CLI `check` command is read-only by default. Pass `--append-result` when the
result should be appended to the `checker_results` ledger and then included in
future reducer snapshots.
