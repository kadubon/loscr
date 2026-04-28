"""Default failure-code transition matrix."""

from __future__ import annotations

from dataclasses import dataclass

from loscr.enums import CheckerStatus, ClaimLevel, FailureFamily, level_at_most
from loscr.models import FailureCode


@dataclass(frozen=True)
class TransitionRule:
    family: FailureFamily
    status: CheckerStatus
    max_supported_level: ClaimLevel
    required_action: str


DEFAULT_TRANSITIONS: dict[FailureFamily, TransitionRule] = {
    FailureFamily.TYPE: TransitionRule(
        FailureFamily.TYPE,
        CheckerStatus.INVALID,
        ClaimLevel.OBSERVABLE,
        "repair schema or create bridge",
    ),
    FailureFamily.MISSING: TransitionRule(
        FailureFamily.MISSING,
        CheckerStatus.DOWNGRADED,
        ClaimLevel.OBSERVABLE,
        "add evidence, reconstruct from signed source, or lower claim",
    ),
    FailureFamily.EPOCH: TransitionRule(
        FailureFamily.EPOCH,
        CheckerStatus.DOWNGRADED,
        ClaimLevel.DESCRIPTIVE,
        "create valid bridge or separate epochs",
    ),
    FailureFamily.INTEGRITY: TransitionRule(
        FailureFamily.INTEGRITY,
        CheckerStatus.QUARANTINED,
        ClaimLevel.DESCRIPTIVE,
        "incident review and revalidation",
    ),
    FailureFamily.PROFILE: TransitionRule(
        FailureFamily.PROFILE,
        CheckerStatus.DOWNGRADED,
        ClaimLevel.CONTROLLED,
        "satisfy profile or narrow claim",
    ),
    FailureFamily.LEDGER: TransitionRule(
        FailureFamily.LEDGER,
        CheckerStatus.DOWNGRADED,
        ClaimLevel.CONTROLLED,
        "reconcile ledger or mark inapplicable before use",
    ),
    FailureFamily.SERVICE: TransitionRule(
        FailureFamily.SERVICE,
        CheckerStatus.DOWNGRADED,
        ClaimLevel.CONTROLLED,
        "reserve capacity, throttle, or recalibrate",
    ),
    FailureFamily.EVALUATOR: TransitionRule(
        FailureFamily.EVALUATOR,
        CheckerStatus.QUARANTINED,
        ClaimLevel.CONTROLLED,
        "stop optimization and pass bridge audit",
    ),
    FailureFamily.BASELINE: TransitionRule(
        FailureFamily.BASELINE,
        CheckerStatus.DOWNGRADED,
        ClaimLevel.AUDITED,
        "repair source, bridge, or narrow target",
    ),
    FailureFamily.FRONTIER: TransitionRule(
        FailureFamily.FRONTIER,
        CheckerStatus.DOWNGRADED,
        ClaimLevel.PRODUCTION_OPERATIONAL,
        "repair frontier source, bridge, or narrow target",
    ),
    FailureFamily.DEPENDENCY: TransitionRule(
        FailureFamily.DEPENDENCY,
        CheckerStatus.DOWNGRADED,
        ClaimLevel.PRODUCTION_OPERATIONAL,
        "expand boundary or audit edge",
    ),
    FailureFamily.ESTIMATOR: TransitionRule(
        FailureFamily.ESTIMATOR,
        CheckerStatus.DOWNGRADED,
        ClaimLevel.AUDITED,
        "use fallback estimator or descriptive report",
    ),
    FailureFamily.HARD_CONSTRAINT: TransitionRule(
        FailureFamily.HARD_CONSTRAINT,
        CheckerStatus.QUARANTINED,
        ClaimLevel.DESCRIPTIVE,
        "rollback, incident closure, and revalidation",
    ),
    FailureFamily.FREEZE: TransitionRule(
        FailureFamily.FREEZE,
        CheckerStatus.DOWNGRADED,
        ClaimLevel.CONTROLLED,
        "exclude frozen periods or bridge restart",
    ),
    FailureFamily.BURDEN: TransitionRule(
        FailureFamily.BURDEN,
        CheckerStatus.DOWNGRADED,
        ClaimLevel.PRODUCTION_OPERATIONAL,
        "charge instrumentation burden or reduce burden",
    ),
}

STATUS_PRIORITY: dict[CheckerStatus, int] = {
    CheckerStatus.VALID: 0,
    CheckerStatus.DOWNGRADED: 1,
    CheckerStatus.QUARANTINED: 2,
    CheckerStatus.INVALID: 3,
}


def failure(
    family: FailureFamily,
    code: str,
    message: str,
    *,
    max_supported_level: ClaimLevel | None = None,
    violated_fields: list[str] | None = None,
    required_action: str | None = None,
) -> FailureCode:
    """Create a failure code with transition defaults attached."""
    rule = DEFAULT_TRANSITIONS[family]
    return FailureCode(
        family=family,
        code=code,
        message=message,
        max_supported_level=max_supported_level or rule.max_supported_level,
        violated_fields=violated_fields or [],
        required_action=required_action or rule.required_action,
    )


def status_for_failures(failures: list[FailureCode]) -> CheckerStatus:
    """Compute the dominant checker status for a set of failure codes."""
    if not failures:
        return CheckerStatus.VALID
    status = CheckerStatus.DOWNGRADED
    for item in failures:
        rule_status = DEFAULT_TRANSITIONS[item.family].status
        if item.family == FailureFamily.MISSING and item.code == "missing_identifier":
            rule_status = CheckerStatus.INVALID
        if item.family == FailureFamily.DEPENDENCY and "hard_stop" in item.code:
            rule_status = CheckerStatus.QUARANTINED
        if item.family == FailureFamily.DEPENDENCY and "incident_reachable" in item.code:
            rule_status = CheckerStatus.QUARANTINED
        if STATUS_PRIORITY[rule_status] > STATUS_PRIORITY[status]:
            status = rule_status
    return status


def cap_level(requested: ClaimLevel, failures: list[FailureCode]) -> ClaimLevel:
    """Apply all failure-code maximum levels to the requested level."""
    supported = requested
    for item in failures:
        cap = item.max_supported_level or DEFAULT_TRANSITIONS[item.family].max_supported_level
        if item.family == FailureFamily.MISSING and item.code == "missing_identifier":
            cap = ClaimLevel.DESCRIPTIVE
        if item.family == FailureFamily.DEPENDENCY and "incident_reachable" in item.code:
            cap = ClaimLevel.DESCRIPTIVE
        supported = level_at_most(supported, cap)
    return supported
