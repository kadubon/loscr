# Layer 0 Quickstart

Layer 0 is the lowest-burden way to use LOSCR. It records factual work events
as sealed local JSONL records and checks whether an `observable` claim is
supported. It does not require service queues, evaluators, baselines, dependency
graphs, replay records, or causal estimators.

Use Layer 0 when you want to answer this narrow question:

> Did this local scope leave enough deterministic evidence to support an
> observable claim?

## Fastest Path

Run the synthetic in-memory demo first:

```bash
uv sync
uv run loscr demo quickstart
uv run loscr demo quickstart --format json
```

The demo uses temporary records only. It shows three outcomes:

- an observable Layer 0 claim that is `valid`;
- a stronger controlled claim that is `downgraded`;
- a corrupted Layer 0 record that is `quarantined`.

## Minimal Ledger Example

Run from the repository root:

```bash
uv run loscr init
uv run loscr ingest jsonl examples/layer0_minimal/edge_events.jsonl --ledger edge_events
uv run loscr reduce
uv run loscr check --claim examples/layer0_minimal/claim_contract.yaml --append-result
uv run loscr reduce
uv run loscr report
```

Expected checker fields:

```text
status: valid
requested_level: observable
supported_level: observable
```

## What To Record

At minimum, each `EdgeEventEnvelope` should have stable identifiers, timestamp,
station, policy, action type, substrate fingerprint, raw status, resource
counts, queue channel and age, dependency flag, reuse count, input/output hashes,
claim scope, and integrity hash.

Prefer hashes for private inputs and outputs. Do not store raw prompts, traces,
diffs, credentials, or local machine paths in public ledgers.

## When To Move Beyond Layer 0

Add the next layer only when the claim requires it:

- controlled: add gate and WIP ledgers;
- service-controlled: add service obligations, reservations, and load contracts;
- audited: add evaluator health and delayed-label evidence;
- production: add baseline, dependency, incident, and checker-result ledgers;
- causal, transfer, frontier, reinvestment: add the corresponding estimator,
  bridge, governance, replay, trusted-base, and lineage evidence.

Requesting a stronger claim before adding that evidence is useful: LOSCR will
return downgrade or quarantine codes instead of silently accepting the claim.
