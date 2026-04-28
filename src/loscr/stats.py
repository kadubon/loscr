"""Deterministic statistical primitives used by LOSCR estimator profiles.

These functions intentionally do not read ledgers or global state. They turn
sealed/logged observations into reproducible diagnostics that can be attached to
`EstimatorProfile.diagnostics` or external audit records.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any, TypeVar

from pydantic import BaseModel

from loscr.hashing import canonical_hash
from loscr.models import (
    AuditBoundInput,
    AuditBoundResult,
    ConfidenceSequenceResult,
    EpsilonDominanceInput,
    EpsilonDominanceResult,
    EstimatorResult,
    FiniteHorizonReinvestmentInput,
    FiniteHorizonReinvestmentResult,
    LoggedPropensityObservation,
    RateImprovementResult,
)


ObservationInput = LoggedPropensityObservation | Mapping[str, Any]
TModel = TypeVar("TModel", bound=BaseModel)


def horvitz_thompson_total(
    observations: Sequence[ObservationInput],
    *,
    estimator_id: str = "horvitz_thompson_total",
    target_mass: float | None = None,
    positivity_floor: float | None = None,
    allow_missing_as_zero: bool = False,
) -> EstimatorResult:
    """Return the design-weighted finite-window total estimate.

    The implementation follows sum A_i Y_i / p_i. Missing audited labels fail
    closed by default because they cannot support strong off-policy or
    sequential claims without a declared missingness rule.
    """
    records = _coerce_observations(observations)
    _validate_positivity_floor(positivity_floor)
    total = 0.0
    variance_upper_bound = 0.0
    used_count = 0
    missing_count = 0
    for record in records:
        _validate_probability(record.assignment_probability, positivity_floor)
        _validate_finite("value", record.value)
        _validate_finite("weight", record.weight)
        if record.missing or record.censored:
            missing_count += 1
            if not allow_missing_as_zero:
                raise ValueError("missing or censored observations require a declared rule")
            continue
        if not record.audited:
            continue
        contribution = record.weight * record.value / record.assignment_probability
        total += contribution
        variance_upper_bound += contribution * contribution
        used_count += 1
    mass = _target_mass(records, target_mass)
    output = EstimatorResult(
        estimator_id=estimator_id,
        estimand="finite_window_total",
        estimate_total=total,
        estimate_mean=total / mass if mass > 0 else None,
        target_mass=mass,
        sample_count=len(records),
        used_count=used_count,
        missing_count=missing_count,
        positivity_floor=positivity_floor,
        variance_upper_bound=variance_upper_bound,
        diagnostics={
            "passed": missing_count == 0 or allow_missing_as_zero,
            "method": "horvitz_thompson",
            "allow_missing_as_zero": allow_missing_as_zero,
        },
    )
    return _with_output_hash(output)


def doubly_robust_total(
    observations: Sequence[ObservationInput],
    *,
    estimator_id: str = "doubly_robust_total",
    target_mass: float | None = None,
    positivity_floor: float | None = None,
    allow_missing_model_fallback: bool = False,
) -> EstimatorResult:
    """Return the finite-window doubly robust total estimate.

    The formula is sum m_hat(x_i) + A_i / p_i * (Y_i - m_hat(x_i)). A valid
    outcome-model value is required for every record.
    """
    records = _coerce_observations(observations)
    _validate_positivity_floor(positivity_floor)
    total = 0.0
    variance_upper_bound = 0.0
    used_count = 0
    missing_count = 0
    for record in records:
        _validate_probability(record.assignment_probability, positivity_floor)
        _validate_finite("value", record.value)
        _validate_finite("weight", record.weight)
        if record.outcome_model_value is None:
            raise ValueError("doubly robust estimate requires outcome_model_value")
        _validate_finite("outcome_model_value", record.outcome_model_value)
        correction = 0.0
        if record.missing or record.censored:
            missing_count += 1
            if not allow_missing_model_fallback:
                raise ValueError("missing or censored observations require a declared rule")
        elif record.audited:
            correction = (record.value - record.outcome_model_value) / record.assignment_probability
            used_count += 1
        contribution = record.weight * (record.outcome_model_value + correction)
        total += contribution
        variance_upper_bound += contribution * contribution
    mass = _target_mass(records, target_mass)
    output = EstimatorResult(
        estimator_id=estimator_id,
        estimand="finite_window_total",
        estimate_total=total,
        estimate_mean=total / mass if mass > 0 else None,
        target_mass=mass,
        sample_count=len(records),
        used_count=used_count,
        missing_count=missing_count,
        positivity_floor=positivity_floor,
        variance_upper_bound=variance_upper_bound,
        diagnostics={
            "passed": missing_count == 0 or allow_missing_model_fallback,
            "method": "doubly_robust",
            "allow_missing_model_fallback": allow_missing_model_fallback,
        },
    )
    return _with_output_hash(output)


def audit_certified_lower_bound(input_data: AuditBoundInput | Mapping[str, Any]) -> AuditBoundResult:
    """Subtract bounded audit debt from accepted value."""
    data = input_data if isinstance(input_data, AuditBoundInput) else AuditBoundInput.model_validate(input_data)
    components = {
        "false_accept_upper_bound": data.false_accept_upper_bound,
        "leakage_upper_bound": data.leakage_upper_bound,
        "missing_certifiedness_upper_bound": data.missing_certifiedness_upper_bound,
    }
    for name, value in data.other_upper_bounds.items():
        if name in components:
            raise ValueError(f"duplicate audit bound component: {name}")
        components[name] = value
    for name, value in components.items():
        _validate_finite(name, value)
        if value < 0:
            raise ValueError(f"{name} must be non-negative")
    _validate_finite("accepted_value", data.accepted_value)
    output = AuditBoundResult(
        accepted_value=data.accepted_value,
        certified_lower_bound=data.accepted_value - sum(components.values()),
        components=components,
    )
    return _with_output_hash(output)


def epsilon_dominance(input_data: EpsilonDominanceInput | Mapping[str, Any]) -> EpsilonDominanceResult:
    """Evaluate deterministic epsilon dominance for value/resource summaries."""
    data = (
        input_data
        if isinstance(input_data, EpsilonDominanceInput)
        else EpsilonDominanceInput.model_validate(input_data)
    )
    for name in (
        "baseline_value",
        "candidate_value",
        "baseline_resource",
        "candidate_resource",
        "value_epsilon",
        "resource_epsilon",
    ):
        _validate_finite(name, float(getattr(data, name)))
    if data.value_epsilon < 0 or data.resource_epsilon < 0:
        raise ValueError("epsilon tolerances must be non-negative")
    value_margin = data.candidate_value - data.baseline_value - data.value_epsilon
    resource_margin = data.candidate_resource - data.baseline_resource - data.resource_epsilon
    blockers: list[str] = []
    if value_margin <= 0:
        blockers.append("value_not_strictly_improved")
    if resource_margin > 0:
        blockers.append("resource_worse_than_tolerance")
    if not data.gate_not_worse:
        blockers.append("gate_profile_worse")
    if not data.wip_not_increased:
        blockers.append("wip_increased")
    if not data.library_liability_not_increased:
        blockers.append("library_liability_increased")
    rate_margin = None
    if data.baseline_resource > 0:
        rate_margin = data.candidate_value - data.baseline_value - (
            data.baseline_value / data.baseline_resource
        ) * (data.candidate_resource - data.baseline_resource)
    output = EpsilonDominanceResult(
        epsilon_dominates=not blockers,
        value_margin=value_margin,
        resource_margin=resource_margin,
        rate_improvement_margin=rate_margin,
        blockers=blockers,
    )
    return _with_output_hash(output)


def rate_improvement_margin(
    *,
    baseline_value: float,
    baseline_resource: float,
    delta_value: float,
    delta_resource: float,
) -> RateImprovementResult:
    """Return the rate-improvement identity margin delta_y - tau delta_r."""
    for name, value in (
        ("baseline_value", baseline_value),
        ("baseline_resource", baseline_resource),
        ("delta_value", delta_value),
        ("delta_resource", delta_resource),
    ):
        _validate_finite(name, value)
    if baseline_resource <= 0:
        raise ValueError("baseline_resource must be positive")
    baseline_rate = baseline_value / baseline_resource
    margin = delta_value - baseline_rate * delta_resource
    output = RateImprovementResult(
        baseline_rate=baseline_rate,
        delta_value=delta_value,
        delta_resource=delta_resource,
        margin=margin,
        improves=margin > 0,
    )
    return _with_output_hash(output)


def finite_horizon_reinvestment_lower_bound(
    input_data: FiniteHorizonReinvestmentInput | Mapping[str, Any],
) -> FiniteHorizonReinvestmentResult:
    """Compute the declared finite-horizon descendant lower bound."""
    data = (
        input_data
        if isinstance(input_data, FiniteHorizonReinvestmentInput)
        else FiniteHorizonReinvestmentInput.model_validate(input_data)
    )
    matrix = data.transition_lower_bound_matrix
    vector = list(data.initial_vector)
    if data.horizon < 0:
        raise ValueError("horizon must be non-negative")
    dimension = len(vector)
    if dimension == 0:
        raise ValueError("initial_vector must be non-empty")
    if len(matrix) != dimension or any(len(row) != dimension for row in matrix):
        raise ValueError("transition_lower_bound_matrix must be square and match initial_vector")
    for index, value in enumerate(vector):
        _validate_finite(f"initial_vector[{index}]", value)
    for row_index, row in enumerate(matrix):
        for column_index, value in enumerate(row):
            _validate_finite(f"matrix[{row_index}][{column_index}]", value)

    per_step_totals: list[float] = []
    current = vector
    if data.include_initial:
        per_step_totals.append(sum(current))
    for _step in range(data.horizon):
        current = _matvec(matrix, current)
        per_step_totals.append(sum(current))
    _validate_finite("lower_bound_offset", data.lower_bound_offset)
    output = FiniteHorizonReinvestmentResult(
        horizon=data.horizon,
        dimension=dimension,
        per_step_totals=per_step_totals,
        terminal_vector=current,
        lower_bound_total=sum(per_step_totals) + data.lower_bound_offset,
    )
    return _with_output_hash(output)


def time_uniform_lower_confidence_bound(
    *,
    cumulative_sum: float,
    variance_upper_bound: float,
    alpha: float = 0.05,
    method: str = "sub_gaussian_conservative",
) -> ConfidenceSequenceResult:
    """Return a conservative deterministic lower confidence-sequence value."""
    _validate_finite("cumulative_sum", cumulative_sum)
    _validate_finite("variance_upper_bound", variance_upper_bound)
    if variance_upper_bound < 0:
        raise ValueError("variance_upper_bound must be non-negative")
    if alpha <= 0 or alpha >= 1:
        raise ValueError("alpha must be in (0, 1)")
    radius = math.sqrt(2.0 * variance_upper_bound * math.log(1.0 / alpha))
    output = ConfidenceSequenceResult(
        method=method,
        alpha=alpha,
        cumulative_sum=cumulative_sum,
        variance_upper_bound=variance_upper_bound,
        radius=radius,
        lower_bound=cumulative_sum - radius,
    )
    return _with_output_hash(output)


def _coerce_observations(observations: Sequence[ObservationInput]) -> list[LoggedPropensityObservation]:
    records = [
        item if isinstance(item, LoggedPropensityObservation) else LoggedPropensityObservation.model_validate(item)
        for item in observations
    ]
    if not records:
        raise ValueError("at least one observation is required")
    return records


def _target_mass(
    records: Sequence[LoggedPropensityObservation], target_mass: float | None
) -> float:
    mass = target_mass if target_mass is not None else sum(record.weight for record in records)
    _validate_finite("target_mass", mass)
    if mass <= 0:
        raise ValueError("target_mass must be positive")
    return mass


def _validate_probability(value: float, positivity_floor: float | None) -> None:
    _validate_finite("assignment_probability", value)
    if value <= 0 or value > 1:
        raise ValueError("assignment_probability must be in (0, 1]")
    if positivity_floor is not None and value < positivity_floor:
        raise ValueError("assignment_probability violates positivity_floor")


def _validate_positivity_floor(value: float | None) -> None:
    if value is None:
        return
    _validate_finite("positivity_floor", value)
    if value <= 0 or value > 1:
        raise ValueError("positivity_floor must be in (0, 1]")


def _validate_finite(name: str, value: float) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")


def _matvec(matrix: Sequence[Sequence[float]], vector: Sequence[float]) -> list[float]:
    return [sum(row[column] * vector[column] for column in range(len(vector))) for row in matrix]


def _with_output_hash(model: TModel) -> TModel:
    return model.model_copy(update={"output_hash": canonical_hash(model)})
