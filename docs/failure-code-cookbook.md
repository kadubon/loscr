# Failure-Code Cookbook

Failure codes are machine-readable evidence controls. Treat them as instructions
for repair, narrowing, downgrade, or quarantine.

## Missing Identifier

- Meaning: a required identifier cannot be reconstructed.
- Typical cause: missing `event_id`, `item_id`, `station_id`, hashes, scope, or
  contract identifier.
- Safe response: repair the source adapter, reconstruct from a signed source, or
  lower the claim to descriptive.
- Unsafe response: inventing identifiers after outcomes are known.
- Affected levels: all non-descriptive levels.

## Missing Non-Identifier Field

- Meaning: a field required by the requested profile is absent.
- Typical cause: missing sidecar, service envelope, evaluator field, or contract
  field.
- Safe response: add the missing evidence, mark it explicitly not applicable, or
  downgrade to a profile that does not use the field.
- Unsafe response: assuming the field is true because the run looked successful.
- Affected levels: the levels whose profiles require the field.

## Schema Or Type Conflict

- Meaning: a record does not match the declared schema.
- Typical cause: wrong enum value, missing required field, wrong data type, or
  extra unsupported field.
- Safe response: fix the adapter or append a corrected record.
- Unsafe response: silently dropping malformed records.
- Affected levels: usually observable or stronger; malformed ingestion becomes
  replay-inert rejection.

## Integrity Failure

- Meaning: a stored hash does not match canonical content.
- Typical cause: edited JSONL line, corrupted replay record, changed contract,
  or broken service/evidence record.
- Safe response: quarantine affected scope, investigate, and append corrected
  evidence after revalidation.
- Unsafe response: editing the hash or mutating old ledger lines.
- Affected levels: all positive credit in affected scope.

## Epoch Without Bridge

- Meaning: material state changed without bridge evidence.
- Typical cause: changed substrate, baseline, evaluator, service envelope,
  frontier source, estimator, or task strata.
- Safe response: create a valid `EpochBridge` or report epochs separately.
- Unsafe response: pooling before/after results into one stronger claim.
- Affected levels: transfer and production-or-stronger comparisons.

## Telemetry Coverage Below Floor

- Meaning: Layer 0 coverage is below the profile floor.
- Typical cause: adapter missing fields, too many missing sidecars, or incomplete
  event reconstruction.
- Safe response: improve telemetry, narrow scope, or downgrade.
- Unsafe response: estimating identifier fields for strong claims.
- Affected levels: observable and stronger, with stricter floors for audited and
  production claims.

## Service Overload Or Missing Service Contract

- Meaning: service capacity evidence is insufficient or overloaded.
- Typical cause: missing load contract, unreserved obligations, held/expired
  work, queue age breach, suspect/quarantined contract, or load above envelope.
- Safe response: reserve capacity, recalibrate load contracts, throttle, narrow
  scope, or downgrade to controlled.
- Unsafe response: excluding backlog or incident exposure from denominators.
- Affected levels: service-controlled and stronger.

## Evaluator Below Floor Or Stale

- Meaning: evaluator health does not meet the requested floor.
- Typical cause: stale audit age, revoked evaluator, unresolved evaluator
  incident, failed canary, leakage signal, or missing evaluator evidence.
- Safe response: stop evaluator-dependent optimization, rerun sentinel audits,
  replace or repair evaluator, then bridge if needed.
- Unsafe response: continuing to optimize against a failed evaluator.
- Affected levels: audited and stronger.

## Baseline Contamination Or Missing Baseline

- Meaning: baseline evidence is absent, contaminated, unbridged, or has material
  debt.
- Typical cause: no shadow or bridged baseline, failed contamination test,
  rolling update after outcomes, or baseline debt above ceiling.
- Safe response: add a shadow/frozen/external baseline, run contamination tests,
  create a bridge, or downgrade to audited.
- Unsafe response: selecting a baseline after seeing outcomes.
- Affected levels: production, transfer, frontier, and reinvestment.

## Frontier Source Or Governance Failure

- Meaning: frontier evidence is not sealed or governed enough.
- Typical cause: missing source ID, missing governance contract, no blinding,
  post-outcome weights, insufficient task mass, failed leakage screen, or weak
  deduplication.
- Safe response: seal the sampling frame, freeze quotas and weights, blind
  outcome-dependent decisions, deduplicate, rerun leakage screens, or downgrade.
- Unsafe response: self-selecting successful frontier tasks.
- Affected levels: frontier and reinvestment paths that rely on frontier claims.

## Dependency Graph Missing Or Unknown Budget Exceeded

- Meaning: dependency coverage is absent or unknown edges exceed the budget.
- Typical cause: missing graph, stale boundary certificate, conservative unknown
  summary edge, or unrecorded dependency.
- Safe response: expand the graph, audit boundary certificates, or narrow scope.
- Unsafe response: declaring dependencies out of scope after an incident.
- Affected levels: production and stronger; zero unknown budget for transfer,
  frontier, and reinvestment.

## Incident Reachable From Claim

- Meaning: an unresolved incident reaches the claim through the dependency graph.
- Typical cause: hard stop, leakage, service quarantine, corrupted replay, or
  trusted-base incident inside the claim scope.
- Safe response: quarantine or narrow affected scope, close incident with
  evidence, and recheck.
- Unsafe response: deleting the incident edge.
- Affected levels: all positive credit in affected scope.

## Hard Stop Reachable

- Meaning: a hard constraint blocks the claim.
- Typical cause: security, permission, leakage, safety, or severe regression
  gate failure.
- Safe response: rollback, quarantine, resolve incident, and revalidate.
- Unsafe response: offsetting a hard stop with scalar gains.
- Affected levels: all positive credit in affected scope.

## Estimator Profile Missing Or Failed

- Meaning: causal, sequential, off-policy, or reinvestment estimate is not
  admissible.
- Typical cause: missing assignment log, positivity floor, outcome cap,
  missingness rule, no-leakage diagnostic, residual/bound diagnostic, or profile
  pass cap below requested level.
- Safe response: use a conservative fallback estimator, add diagnostics, lower
  the claim, or report descriptive evidence only.
- Unsafe response: treating a point estimate as causal evidence without design
  logs.
- Affected levels: production-causal and reinvestment; sometimes audited
  off-policy claims.

## Corrupted Replay

- Meaning: replay or library evidence is corrupted or quarantined.
- Typical cause: invalid replay hash, revoked trusted base, stale maintenance,
  or quarantined library entry.
- Safe response: quarantine entry, refresh replay, repair trusted base, or
  retire the artifact.
- Unsafe response: counting a corrupted artifact as reusable capital.
- Affected levels: production, transfer, frontier, and reinvestment when they
  depend on replay.

## Trusted Base Revoked Or Stale

- Meaning: a relevant trusted-base entry is not active.
- Typical cause: revoked checker, out-of-scope trusted base, stale audit, or
  failed registry validation.
- Safe response: replace trusted base, rerun registry audit, bridge if needed,
  and recheck reachable claims.
- Unsafe response: pinning to an old trusted base after revocation.
- Affected levels: production and stronger claims that depend on it.

## Instrumentation Burden Uncharged

- Meaning: measurement overhead exceeded the ceiling and was not charged.
- Typical cause: excessive tokens, wall time, compute, storage, or manual
  annotation cost.
- Safe response: charge the burden, reduce instrumentation cost, or lower the
  claim.
- Unsafe response: reporting productivity gain without measurement overhead.
- Affected levels: production and dramatic acceleration claims.

## Freeze Without Sequential Monitoring Profile

- Meaning: a frozen period exists without a sealed sequential profile.
- Typical cause: confidence updates failed, missing outcomes, or online monitor
  freeze without profile evidence.
- Safe response: add a valid `SequentialMonitoringProfile`, exclude frozen
  intervals, or bridge restart conditions.
- Unsafe response: counting frozen periods as successful active horizon.
- Affected levels: production and stronger.

## Reinvestment Lineage Unbounded

- Meaning: reinvestment credit lacks bounded lineage evidence.
- Typical cause: descriptive lineage only, unattributed co-use, no signed
  lineage, no negative-lineage audit, no finite-horizon lower bound, or stale
  maintenance.
- Safe response: add signed lineage, marginal or cohort-bounded attribution,
  negative-lineage audit, maintenance charges, and finite-horizon lower bound.
- Unsafe response: counting admitted, experimental, downgraded, or co-used
  artifacts as independent reusable capital.
- Affected levels: reinvestment.
