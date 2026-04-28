"""Convenience helpers for sealing and verifying LOSCR records."""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel

from loscr.hashing import compute_integrity_hash, verify_integrity_hash


T = TypeVar("T", bound=BaseModel)


def seal_model(model: T) -> T:
    """Return a copy of a Pydantic record with its integrity hash recomputed."""
    if "integrity_hash" not in type(model).model_fields:
        return model
    return model.model_copy(update={"integrity_hash": compute_integrity_hash(model)})


def seal_data(data: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of a mapping with a canonical integrity hash."""
    sealed = dict(data)
    sealed["integrity_hash"] = compute_integrity_hash(sealed)
    return sealed


def is_sealed(record: BaseModel | dict[str, Any]) -> bool:
    """Return true when a record carries a valid LOSCR integrity hash."""
    return verify_integrity_hash(record)
