from dataclasses import dataclass
from core.utils.vec2 import Vec2


@dataclass
class MoveAction:
    """Body a move action of a combat unit to a position."""

    unit_id: int
    to: Vec2


@dataclass
class GroupMoveAction:
    """Body a group move action consisting of multiple move actions."""

    actions: list[MoveAction]


@dataclass
class MoveActionResult:
    """Result of a move action whether is valid or interrupted."""

    is_valid: bool
    is_interrupted: bool = False


@dataclass
class MoveActionLog:
    """Log of a move action. Defines whether is valid or whether is interrupted."""

    action: MoveAction
    is_valid: bool
    is_interrupted: bool = False


@dataclass
class GroupMoveActionLog:
    """Log of group move action consisting of multiple move action logs."""

    moveActionLogs: list[MoveActionLog]
