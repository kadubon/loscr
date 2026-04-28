"""LOSCR reference implementation."""

from loscr.checker.core import check
from loscr.hashing import canonical_hash, canonical_json, compute_integrity_hash
from loscr.integrity import is_sealed, seal_data, seal_model
from loscr.model_registry import get_model, model_names, seal_record
from loscr.state import build_snapshot, context_from_store
from loscr.stats import (
    audit_certified_lower_bound,
    doubly_robust_total,
    epsilon_dominance,
    finite_horizon_reinvestment_lower_bound,
    horvitz_thompson_total,
    rate_improvement_margin,
    time_uniform_lower_confidence_bound,
)
from loscr.storage import JsonlLedgerStore

__all__ = [
    "JsonlLedgerStore",
    "audit_certified_lower_bound",
    "canonical_hash",
    "canonical_json",
    "check",
    "build_snapshot",
    "context_from_store",
    "compute_integrity_hash",
    "doubly_robust_total",
    "epsilon_dominance",
    "finite_horizon_reinvestment_lower_bound",
    "get_model",
    "horvitz_thompson_total",
    "is_sealed",
    "model_names",
    "rate_improvement_margin",
    "seal_data",
    "seal_model",
    "seal_record",
    "time_uniform_lower_confidence_bound",
]

__version__ = "0.1.0"
