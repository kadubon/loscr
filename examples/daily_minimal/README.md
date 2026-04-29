# Daily Minimal Example

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
uv run loscr check --claim examples/daily_minimal/claim_contract.yaml --append-result
uv run loscr reduce
uv run loscr report
```
