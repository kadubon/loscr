"""Evaluator reducer extension point for LOSCR MVP."""

from __future__ import annotations

from loscr.hashing import canonical_hash
from loscr.models import EvaluatorHealth


def evaluator_reducer(health: list[EvaluatorHealth]) -> dict[str, object]:
    """Return deterministic evaluator state data for current MVP checks."""
    payload = {item.evaluator_id: item.model_dump(mode="json") for item in health}
    return {"evaluators": payload, "output_hash": canonical_hash(payload)}
