# Schemas

Export schemas with:

```bash
uv run loscr schema export --out schemas/
```

Schemas are generated from Pydantic v2 models and enums. Unknown fields are
forbidden so other agents can distinguish unsupported data from accepted data.
The export includes ledger models, reducer outputs, checker inputs/results,
rejection records, extension contracts, deterministic estimator/math result
models, and enum schemas.

To create sealed local records without writing custom code:

```bash
uv run loscr seal claim.yaml --model ClaimContract --out claim.sealed.json
```

Dynamic tools can use `loscr.model_registry.model_names()` and
`loscr.model_registry.seal_record()` to discover model classes and recompute
integrity hashes without importing individual schemas.

Service-control schemas include service ledger events, obligations, load
contracts, and capacity envelopes. Stronger claim contracts should reference
service envelopes and keep the corresponding load-contract ledger available in
the local store.
