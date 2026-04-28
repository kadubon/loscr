# Adapters

Adapters map local operational logs into LOSCR records.

- `jsonl.py`: generic local JSONL ingestion.
- `git.py`: local git CLI only; hashes commit/tree/diff metadata by default.
- `junit.py`: JUnit XML test results.
- `llm_tool_log.py`: local JSONL LLM/tool-call logs with prompt and tool hashes.

Adapters must not require external APIs or network access.

For custom adapters, register a local callable with `AdapterRegistry` from
`loscr.adapters.registry`. Adapter output should be Pydantic LOSCR records so it
can be appended with `JsonlLedgerStore`.

Adapter contracts are represented by `AdapterContract` and exported as JSON
Schema. Use `default_adapter_contracts()` from `loscr.adapters.contracts` as the
starting point for local conformance tests.

Reducers have a parallel discovery surface in `loscr.reducers.registry`.
`default_reducer_registry()` returns reducer metadata, input ledgers, output
models, and a deterministic registry hash. Custom reducers should register a
`ReducerSpec` and keep the reducer function pure and replayable from explicit
ledger records.

The default registry includes telemetry, gate, WIP, service, resource,
delayed-label, pressure, artifact, baseline, dependency, library, exploration,
and claim reducers. Projects can adopt only the low-cost telemetry/gate/WIP
subset first, then add service, evaluator, replay, frontier, or reinvestment
ledgers when stronger claim levels are requested.
