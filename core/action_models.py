from dataclasses import dataclass
from enum import Enum


class FireOutcomes(str, Enum):
    """Defines all fire outcomes."""

    MISS = "MISS"
    PIN = "PIN"
    SUPPRESS = "SUPPRESS"
    KILL = "KILL"


class FireOutcomesChances(float, Enum):
    """Maps each fire outcome to its probability range"""

    MISS = 0.3
    PIN = 0.7
    SUPPRESS = 0.95
    KILL = 1.0


class AssaultOutcomes(str, Enum):
    """Defines an assault outcome as fail or success."""

    FAIL = "FAIL"
    SUCCESS = "SUCCESS"


class AssaultSuccessChances(float, Enum):
    """Maps each target status to its assault success chance."""

    ACTIVE = 0.5
    PINNED = 0.7
    SUPPRESSED = 0.95


@dataclass
class MoveActionResult:
    """Result of a move action as any reactive fire."""

    reactive_fire_outcome: FireOutcomes | None = None


@dataclass
class GroupMoveActionResult:
    """Result of a group move action as multiple singular move results."""

    moveActionLogs: list[MoveActionResult]


@dataclass
class FireActionResult:
    """Result of a fire action as outcome."""

    outcome: FireOutcomes | None = None


@dataclass
class AssaultActionResult:
    """Result of an assault action as assault outcome, and any reactive fire."""

    outcome: AssaultOutcomes | None = None
    reactive_fire_outcome: FireOutcomes | None = None


class InvalidActionTypes(str, Enum):
    """Different types of invalid (not error) actions."""

    BAD_INITIATIVE = "BAD_INITIATIVE"
    BAD_ENTITY = "BAD_ENTITY"
    BAD_COORDS = "BAD_COORDS"
