from dataclasses import dataclass

from core.gamestate import GameState
from core.models.outcomes import AssaultOutcomes, FireOutcomes
from core.models.vec2 import Vec2


@dataclass
class MoveAction:
    """Request model for a unit's move action."""

    unit_id: int
    to: Vec2


@dataclass
class FireAction:
    """Request model for a unit's fire action."""

    unit_id: int
    target_id: int


@dataclass
class AssaultAction:
    """Request model for a unit's assault action."""

    unit_id: int
    target_id: int


@dataclass
class MoveActionResult:
    action: MoveAction
    result_gs: GameState
    reactive_fire_outcome: FireOutcomes | None = None


@dataclass
class FireActionResult:
    action: FireAction
    result_gs: GameState
    outcome: FireOutcomes | None = None


@dataclass
class AssaultActionResult:
    action: AssaultAction
    result_gs: GameState
    outcome: AssaultOutcomes | None = None
    reactive_fire_outcome: FireOutcomes | None = None


ActionResult = MoveActionResult | FireActionResult | AssaultActionResult
