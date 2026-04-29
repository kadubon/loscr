# GitHub Actions

LOSCR can run safely in public CI when it uses synthetic fixtures and does not
upload private ledgers, prompts, traces, or diffs.

## Minimal CI

```yaml
name: loscr

on:
  push:
  pull_request:

jobs:
  loscr:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        uses: astral-sh/setup-uv@v5
      - name: Sync
        run: uv sync --all-extras --dev
      - name: Ruff
        run: uv run ruff check .
      - name: Mypy
        run: uv run mypy src
      - name: Pytest
        run: uv run pytest
      - name: Quickstart demo
        run: uv run loscr demo quickstart --format json
      - name: Initialize LOSCR store
        run: uv run loscr init
      - name: Doctor
        run: uv run loscr doctor
```

`loscr doctor` expects a local store. Run `loscr init` first in fresh CI
workspaces. The quickstart demo uses temporary synthetic records only, so it
does not upload or inspect private ledgers.

## Conformance Workflow

```yaml
- name: Synthetic conformance
  run: uv run loscr conformance run examples/synthetic_conformance
```

Use public synthetic fixtures in public CI. They exercise downgrade, invalid,
and quarantine behavior without private evidence.

## Public-Release Audit

```yaml
- name: Public audit
  run: uv run loscr audit-public
```

This lightweight audit scans public text files for high-confidence secrets and
local personal paths. It does not replace a dedicated secret scanner for
regulated or commercial releases.

## Private Evidence

- Do not upload private `.loscr/ledgers/` artifacts from public CI.
- Do not commit raw prompts, raw traces, raw diffs, credentials, or personal
  local paths.
- Use hashes and protected trace hashes in public examples.
- Run private ledgers only in private CI contexts with access control and
  retention policy.
- If a private workflow publishes `CheckerResult` artifacts, include the state
  hash, checker version hash, profile registry version, and trusted-base
  registry version.
