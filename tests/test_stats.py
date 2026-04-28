from __future__ import annotations

import pytest

from loscr.models import (
    AuditBoundInput,
    EpsilonDominanceInput,
    FiniteHorizonReinvestmentInput,
    LoggedPropensityObservation,
)
from loscr.stats import (
    audit_certified_lower_bound,
    doubly_robust_total,
    epsilon_dominance,
    finite_horizon_reinvestment_lower_bound,
    horvitz_thompson_total,
    rate_improvement_margin,
    time_uniform_lower_confidence_bound,
)


def _observation(**overrides: object) -> LoggedPropensityObservation:
    data: dict[str, object] = {
        "observation_id": "obs-1",
        "assignment_probability": 0.5,
        "value": 10.0,
    }
    data.update(overrides)
    return LoggedPropensityObservation.model_validate(data)


def test_horvitz_thompson_total_is_deterministic() -> None:
    result = horvitz_thompson_total([_observation()], positivity_floor=0.1)
    repeated = horvitz_thompson_total([_observation()], positivity_floor=0.1)
    assert result.estimate_total == 20.0
    assert result.estimate_mean == 20.0
    assert result.output_hash == repeated.output_hash
    assert result.diagnostics["passed"] is True


def test_horvitz_thompson_rejects_missing_by_default() -> None:
    with pytest.raises(ValueError, match="missing"):
        horvitz_thompson_total([_observation(missing=True)])


def test_doubly_robust_total_uses_model_residual_correction() -> None:
    result = doubly_robust_total([_observation(outcome_model_value=8.0)])
    assert result.estimate_total == 12.0
    assert result.diagnostics["method"] == "doubly_robust"


def test_audit_certified_lower_bound_subtracts_debt() -> None:
    result = audit_certified_lower_bound(
        AuditBoundInput(
            accepted_value=10.0,
            false_accept_upper_bound=1.0,
            leakage_upper_bound=0.5,
            missing_certifiedness_upper_bound=0.25,
        )
    )
    assert result.certified_lower_bound == 8.25
    assert result.output_hash.startswith("sha256:")


def test_epsilon_dominance_and_rate_margin() -> None:
    result = epsilon_dominance(
        EpsilonDominanceInput(
            baseline_value=10.0,
            candidate_value=12.0,
            baseline_resource=5.0,
            candidate_resource=4.5,
            value_epsilon=0.5,
        )
    )
    assert result.epsilon_dominates is True
    margin = rate_improvement_margin(
        baseline_value=10.0,
        baseline_resource=5.0,
        delta_value=2.0,
        delta_resource=-0.5,
    )
    assert margin.improves is True


def test_finite_horizon_reinvestment_lower_bound() -> None:
    result = finite_horizon_reinvestment_lower_bound(
        FiniteHorizonReinvestmentInput(
            transition_lower_bound_matrix=[[0.0, 0.0], [0.5, 0.0]],
            initial_vector=[1.0, 0.0],
            horizon=2,
        )
    )
    assert result.per_step_totals == [0.5, 0.0]
    assert result.lower_bound_total == 0.5


def test_time_uniform_lower_confidence_bound() -> None:
    result = time_uniform_lower_confidence_bound(
        cumulative_sum=10.0, variance_upper_bound=4.0, alpha=0.05
    )
    assert result.lower_bound < 10.0
    assert result.radius > 0.0
