# Operations

LOSCR is intentionally local-first, but operational meaning comes from local
policy. Before using LOSCR to support strong claims, record the following
decisions in `.loscr/config.yaml`, a repository policy file, or an internal
governance record.

## Minimum Deployment

1. Define claim scopes, station names, task strata, and claim owners.
2. Register adapters and decide which raw fields are stored versus hashed.
3. Enable Layer 0 ledgers and verify deterministic replay on a small prefix.
4. Add gate and WIP ledgers before claiming controlled operation.
5. Add service obligations, service load contracts, and service envelopes before
   claiming service-controlled or stronger results.
6. Add evaluator health, delayed-label, baseline, dependency, and checker-result
   ledgers before production claims.
7. Add estimator profiles, frontier governance, trusted-base registries, replay
   records, and lineage ledgers only when the corresponding strong claim needs
   them.

For a low-friction trial, start with `examples/layer0_minimal/` or
`uv run loscr demo quickstart`. Do not add service, evaluator, baseline, or
library obligations until the organization is ready to make the corresponding
stronger claim.

## Required Local Policies

- Adapter policy: field maps, stable IDs, timestamp source, privacy filter, and
  maximum supported claim level.
- Service policy: service channels, units, reservations, age envelopes, load
  contract calibration, and overload actions.
- Evaluator policy: evaluator floor by claim level, canary budget, sentinel
  audit cadence, leakage probes, and revocation triggers.
- Baseline policy: baseline type, assignment rule, bridge rule, contamination
  tests, update cadence, and debt ceiling.
- Dependency policy: graph boundary, unknown-edge budget, boundary certificate
  cadence, hard-stop types, and incident closure criteria.
- Estimator policy: assignment logging, positivity floor, outcome cap,
  missingness rule, interference handling, uncertainty rule, and diagnostics.
- Frontier policy: source admission, quota freeze, pre-outcome weights,
  blinding, deduplication, leakage screening, task mass, and dispute handling.
- Library policy: trusted-base validation, replay tier, maintenance due time,
  promotion evidence, signed lineage, negative-lineage audit, and retirement.
- Security policy: secret scanning, raw-content exceptions, signing, retention,
  access control, release review, and vulnerability reporting.

## Commercial Use Notes

LOSCR can make claim evidence replayable and machine-checkable, but it does not
replace legal, security, safety, privacy, or statistical review. A commercial
deployment should keep raw private content out of ledgers by default, restrict
who can append strong-claim records, run an external secret scanner before
release, and treat every downgrade or quarantine as an operational action item.

Strong claims should be presented with the exact `CheckerResult`, state hash,
checker version hash, ledger prefix, profile registry, trusted-base registry,
and local policy version used to support them.
