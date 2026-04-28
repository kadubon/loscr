# Security Policy

LOSCR is local-first and makes no network calls at runtime by default.

Do not commit secrets, local absolute paths, private raw prompts, private raw
diffs, or API keys. Adapters should hash sensitive content unless a caller
explicitly opts into preserving raw content.

Before publishing a release, run:

```bash
uv run loscr audit-public
```

The audit is intentionally lightweight. It detects high-confidence private key
blocks, common service token prefixes, and personal machine paths. It does not
replace a dedicated secret scanner for regulated environments.

Report security issues through the repository's private vulnerability reporting
channel when available.
