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
    """Result of a move action whether is valid or interrupted."""

    is_valid: bool
    reactive_fire_outcome: FireControls.Outcomes | None = None


@dataclass
class MoveActionLog:
    """Log of a move action. Defines whether is valid or whether is interrupted."""

    action: MoveAction
    result: MoveActionResult


@dataclass
class GroupMoveActionLog:
    """Log of group move action consisting of multiple move action logs."""

    moveActionLogs: list[MoveActionLog]
