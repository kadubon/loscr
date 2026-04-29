# Layer 0 Minimal Example

This example shows the smallest useful LOSCR path: one sealed Layer 0 edge
event and one observable claim contract. It proves only that the local ledger
supports an `observable` claim. It does not support controlled, audited,
production, causal, frontier, or reinvestment claims.

Run from the repository root:

```bash
uv sync
uv run loscr init
uv run loscr ingest jsonl examples/layer0_minimal/edge_events.jsonl --ledger edge_events
uv run loscr reduce
uv run loscr check --claim examples/layer0_minimal/claim_contract.yaml --append-result
uv run loscr reduce
uv run loscr report
```

Expected result: `loscr check` returns `status=valid` and
`supported_level=observable`. If you request a stronger claim without adding
gate, WIP, service, evaluator, baseline, dependency, or replay evidence, LOSCR
will downgrade or quarantine the claim instead of interpreting it optimistically.
