from dataclasses import dataclass
from enum import Enum


@dataclass
class AssaultAction:
    """An assault action of attacker combat unit assaulting target unit."""

    attacker_id: int
    target_id: int


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

    INACTIVE_UNIT = "INACTIVE_UNIT"
    NO_INITIATIVE = "NO_INITIATIVE"
    BAD_ENTITY = "BAD_ENTITY"
    BAD_COORDS = "BAD_COORDS"
