from core.components import AssaultControls, FireControls
from core.utils.vec2 import Vec2
from dataclasses import dataclass
from enum import Enum


@dataclass
class MoveAction:
    """A singular move action of a combat unit to a position."""

    unit_id: int
    to: Vec2


@dataclass
class GroupMoveAction:
    """A group move action consisting of multiple move actions."""

    moves: list[MoveAction]


@dataclass
class AssaultAction:
    """An assault action of attacker combat unit assaulting target unit."""

    attacker_id: int
    target_id: int


@dataclass
class FireAction:
    """A fire action of attacker combat unit firing at target unit."""

    attacker_id: int
    target_id: int


@dataclass
class MoveActionResult:
    """Result of a move action as any reactive fire."""

    reactive_fire_outcome: FireControls.Outcomes | None = None


@dataclass
class GroupMoveActionResult:
    """Result of a group move action as multiple singular move results."""

    moveActionLogs: list[MoveActionResult]


@dataclass
class FireActionResult:
    """Result of a fire action as validity and fire action outcome."""

    outcome: FireControls.Outcomes | None = None


@dataclass
class AssaultActionResult:
    """Result of an assault action as assault outcome, and any reactive fire."""

    outcome: AssaultControls.Outcomes | None = None
    reactive_fire_outcome: FireControls.Outcomes | None = None


class InvalidActionTypes(str, Enum):
    """Different types of invalid (not error) actions."""

    BAD_INITIATIVE = "BAD_INITIATIVE"
    BAD_ENTITY = "BAD_ENTITY"
    BAD_COORDS = "BAD_COORDS"
