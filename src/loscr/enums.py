"""String enums used by LOSCR schemas and checker rules."""

from enum import StrEnum


class ClaimLevel(StrEnum):
    DESCRIPTIVE = "descriptive"
    OBSERVABLE = "observable"
    CONTROLLED = "controlled"
    SERVICE_CONTROLLED = "service_controlled"
    AUDITED = "audited"
    PRODUCTION_OPERATIONAL = "production_operational"
    PRODUCTION_CAUSAL = "production_causal"
    TRANSFER = "transfer"
    FRONTIER = "frontier"
    REINVESTMENT = "reinvestment"


CLAIM_LEVEL_ORDER: tuple[ClaimLevel, ...] = (
    ClaimLevel.DESCRIPTIVE,
    ClaimLevel.OBSERVABLE,
    ClaimLevel.CONTROLLED,
    ClaimLevel.SERVICE_CONTROLLED,
    ClaimLevel.AUDITED,
    ClaimLevel.PRODUCTION_OPERATIONAL,
    ClaimLevel.PRODUCTION_CAUSAL,
    ClaimLevel.TRANSFER,
    ClaimLevel.FRONTIER,
    ClaimLevel.REINVESTMENT,
)


class ClaimForm(StrEnum):
    DESCRIPTIVE = "descriptive"
    OPERATIONAL = "operational"
    CAUSAL = "causal"
    TRANSFER = "transfer"
    FRONTIER = "frontier"
    REINVESTMENT = "reinvestment"


class CheckerStatus(StrEnum):
    VALID = "valid"
    INVALID = "invalid"
    DOWNGRADED = "downgraded"
    QUARANTINED = "quarantined"


class FailureFamily(StrEnum):
    TYPE = "type"
    MISSING = "missing"
    EPOCH = "epoch"
    INTEGRITY = "integrity"
    PROFILE = "profile"
    LEDGER = "ledger"
    SERVICE = "service"
    EVALUATOR = "evaluator"
    BASELINE = "baseline"
    FRONTIER = "frontier"
    DEPENDENCY = "dependency"
    ESTIMATOR = "estimator"
    HARD_CONSTRAINT = "hard_constraint"
    FREEZE = "freeze"
    BURDEN = "burden"


class ServiceContractState(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPECT = "suspect"
    QUARANTINED = "quarantined"
    RECALIBRATED = "recalibrated"


class ServiceObligationStatus(StrEnum):
    CREATED = "created"
    RESERVED = "reserved"
    IN_SERVICE = "in_service"
    COMPLETED = "completed"
    HELD = "held"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    QUARANTINED = "quarantined"


class EvaluatorState(StrEnum):
    UNTRUSTED = "untrusted"
    MONITORED = "monitored"
    AUDITED = "audited"
    BRIDGED = "bridged"
    REVOKED = "revoked"


EVALUATOR_STATE_ORDER: tuple[EvaluatorState, ...] = (
    EvaluatorState.UNTRUSTED,
    EvaluatorState.MONITORED,
    EvaluatorState.AUDITED,
    EvaluatorState.BRIDGED,
    EvaluatorState.REVOKED,
)


class GateState(StrEnum):
    PASS = "pass"
    WARN = "warn"
    QUARANTINE = "quarantine"
    ROLLBACK = "rollback"
    HARD_STOP = "hard_stop"


class ItemState(StrEnum):
    CREATED = "created"
    ACTIVE = "active"
    SUBMITTED = "submitted"
    CERTIFIED = "certified"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    EXPIRED = "expired"
    QUARANTINED = "quarantined"


class FieldStatus(StrEnum):
    OBSERVED = "observed"
    MISSING = "missing"
    NOT_APPLICABLE = "not_applicable"
    ESTIMATED = "estimated"


class ReplayTier(StrEnum):
    HASH = "hash"
    CONTAINER = "container"
    SEMANTIC = "semantic"
    STATISTICAL = "statistical"


class TrustedBaseState(StrEnum):
    ACTIVE = "active"
    REVOKED = "revoked"
    OUT_OF_SCOPE = "out_of_scope"
    STALE = "stale"


class LibraryState(StrEnum):
    CANDIDATE = "candidate"
    EXPERIMENTAL = "experimental"
    ADMITTED = "admitted"
    PROMOTED = "promoted"
    DUE = "due"
    DOWNGRADED = "downgraded"
    QUARANTINED = "quarantined"
    RETIRED = "retired"


def claim_level_index(level: ClaimLevel) -> int:
    """Return the total-order index for a claim level."""
    return CLAIM_LEVEL_ORDER.index(level)


def min_claim_level(*levels: ClaimLevel) -> ClaimLevel:
    """Return the weakest level from one or more claim levels."""
    if not levels:
        return ClaimLevel.DESCRIPTIVE
    return min(levels, key=claim_level_index)


def max_claim_level(*levels: ClaimLevel) -> ClaimLevel:
    """Return the strongest level from one or more claim levels."""
    if not levels:
        return ClaimLevel.DESCRIPTIVE
    return max(levels, key=claim_level_index)


def level_at_most(level: ClaimLevel, cap: ClaimLevel) -> ClaimLevel:
    """Cap a claim level at a maximum supported level."""
    return min_claim_level(level, cap)


def level_gte(level: ClaimLevel, floor: ClaimLevel) -> bool:
    """Return true when level is at least as strong as floor."""
    return claim_level_index(level) >= claim_level_index(floor)


def evaluator_state_gte(state: EvaluatorState, floor: EvaluatorState) -> bool:
    """Return true when an evaluator state satisfies a floor."""
    if state == EvaluatorState.REVOKED:
        return floor == EvaluatorState.REVOKED
    if floor == EvaluatorState.REVOKED:
        return state == EvaluatorState.REVOKED
    return EVALUATOR_STATE_ORDER.index(state) >= EVALUATOR_STATE_ORDER.index(floor)
