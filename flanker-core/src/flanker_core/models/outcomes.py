from dataclasses import dataclass
from enum import Enum


class AssaultOutcomes(str, Enum):
    """Defines an assault outcome as fail or success."""

    FAIL = "FAIL"
    SUCCESS = "SUCCESS"


class FireOutcomes(str, Enum):
    """Defines all fire outcomes."""

    MISS = "MISS"
    PIN = "PIN"
    SUPPRESS = "SUPPRESS"
    KILL = "KILL"


class FireEffect(str, Enum):
    """Defines all fire effects."""

    PINNING = "PINNING"
    SUPPRESSING = "SUPPRESSING"


class InvalidAction(str, Enum):
    """Defines reasons of invalid (not error) actions."""

    INACTIVE_UNIT = "INACTIVE_UNIT"
    NO_INITIATIVE = "NO_INITIATIVE"
    BAD_ENTITY = "BAD_ENTITY"
    BAD_COORDS = "BAD_COORDS"


@dataclass
class MoveActionResult:
    """Result of a move action as any reactive fire."""

    reactive_fire_outcome: FireOutcomes | None = None
