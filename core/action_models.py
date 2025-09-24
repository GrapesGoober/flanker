from dataclasses import dataclass
from core.components import FireControls
from core.utils.vec2 import Vec2


@dataclass
class MoveAction:
    """Body a move action of a combat unit to a position."""

    unit_id: int
    to: Vec2


@dataclass
class GroupMoveAction:
    """Body a group move action consisting of multiple move actions."""

    moves: list[MoveAction]


@dataclass
class MoveActionResult:
    """Result of a move action as validity and any reactive fire."""

    is_valid: bool
    reactive_fire_outcome: FireControls.Outcomes | None = None


@dataclass
class GroupMoveActionResult:
    """Result of a group move action as multiple singular move results."""

    moveActionLogs: list[MoveActionResult]
