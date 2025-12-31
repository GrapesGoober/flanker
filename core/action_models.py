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


class InvalidActionTypes(str, Enum):
    """Different types of invalid (not error) actions."""

    INACTIVE_UNIT = "INACTIVE_UNIT"
    NO_INITIATIVE = "NO_INITIATIVE"
    BAD_ENTITY = "BAD_ENTITY"
    BAD_COORDS = "BAD_COORDS"
