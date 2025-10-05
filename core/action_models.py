from enum import Enum


class InvalidActionTypes(str, Enum):
    """Different types of invalid (not error) actions."""

    INACTIVE_UNIT = "INACTIVE_UNIT"
    NO_INITIATIVE = "NO_INITIATIVE"
    BAD_ENTITY = "BAD_ENTITY"
    BAD_COORDS = "BAD_COORDS"
