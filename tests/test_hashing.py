from __future__ import annotations

from loscr.hashing import canonical_hash, canonical_json, compute_integrity_hash


def test_canonical_hashes_are_stable() -> None:
    left = {"b": [2, 1], "a": {"x": 1}}
    right = {"a": {"x": 1}, "b": [2, 1]}
    assert canonical_json(left) == canonical_json(right)
    assert canonical_hash(left) == canonical_hash(right)


def test_integrity_hash_omits_integrity_fields() -> None:
    base = {"event_id": "e1", "integrity_hash": "wrong", "nested": {"integrity_hash": "x"}}
    changed = {"event_id": "e1", "integrity_hash": "other", "nested": {"integrity_hash": "y"}}
    assert compute_integrity_hash(base) == compute_integrity_hash(changed)
