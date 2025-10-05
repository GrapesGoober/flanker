from enum import Enum


class FireOutcomes(str, Enum):
    """Defines all fire outcomes."""

    MISS = "MISS"
    PIN = "PIN"
    SUPPRESS = "SUPPRESS"
    KILL = "KILL"


class AssaultOutcomes(str, Enum):
    """Defines an assault outcome as fail or success."""

    FAIL = "FAIL"
    SUCCESS = "SUCCESS"


class InvalidActionTypes(str, Enum):
    """Different types of invalid (not error) actions."""

    BAD_INITIATIVE = "BAD_INITIATIVE"
    BAD_ENTITY = "BAD_ENTITY"
    BAD_COORDS = "BAD_COORDS"
