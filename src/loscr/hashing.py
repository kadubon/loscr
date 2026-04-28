"""Deterministic canonical JSON and hash helpers."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from enum import Enum
from math import isfinite
from typing import Any

from pydantic import BaseModel


HASH_PREFIX = "sha256:"


def _normalize(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return _normalize(value.model_dump(mode="json", exclude_none=False))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _normalize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError("canonical JSON does not allow NaN or infinite floats")
        return value
    return value


def _drop_integrity_hashes(value: Any) -> Any:
    normalized = _normalize(value)
    if isinstance(normalized, dict):
        return {
            key: _drop_integrity_hashes(item)
            for key, item in normalized.items()
            if key != "integrity_hash"
        }
    if isinstance(normalized, list):
        return [_drop_integrity_hashes(item) for item in normalized]
    return normalized


def canonical_json(value: Any) -> str:
    """Return deterministic canonical JSON for supported Python/Pydantic values."""
    return json.dumps(
        _normalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def canonical_hash(value: Any) -> str:
    """Return a SHA-256 hash over canonical JSON."""
    payload = canonical_json(value).encode("utf-8")
    return f"{HASH_PREFIX}{hashlib.sha256(payload).hexdigest()}"


def compute_integrity_hash(value: Any) -> str:
    """Hash a record after recursively omitting every field named ``integrity_hash``."""
    return canonical_hash(_drop_integrity_hashes(value))


def attach_integrity_hash(record: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of a mapping with a computed integrity hash."""
    copy = dict(record)
    copy["integrity_hash"] = compute_integrity_hash(copy)
    return copy


def verify_integrity_hash(value: Any) -> bool:
    """Return true when a record's stored integrity hash matches canonical content."""
    normalized = _normalize(value)
    if not isinstance(normalized, dict):
        return False
    stored = normalized.get("integrity_hash")
    return isinstance(stored, str) and stored == compute_integrity_hash(normalized)
