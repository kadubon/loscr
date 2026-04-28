"""Generic JSONL ingestion adapter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_jsonl_records(path: str | Path) -> list[dict[str, Any]]:
    """Read local JSONL records without network access."""
    records: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            payload = json.loads(stripped)
            if not isinstance(payload, dict):
                raise ValueError(f"line {line_number} is not a JSON object")
            records.append(payload)
    return records
