# Conformance

Synthetic conformance fixtures cover:

- missing identifier
- stale evaluator
- service overload
- baseline contamination
- corrupted replay
- hard-stop dependency reachability

Run:

```bash
uv run pytest tests/test_conformance_*.py
uv run loscr conformance run examples/synthetic_conformance
```

Each fixture directory may contain a `fixture.yaml` with a sealed `ClaimContract`,
a compact checker context, and an expected checker status/failure code.

Additional unit conformance tests cover transfer bridge absence, frontier
governance absence, causal estimator profile absence, unbounded reinvestment
lineage, revoked trusted-base entries, and freeze handling without a sequential
monitoring profile.
