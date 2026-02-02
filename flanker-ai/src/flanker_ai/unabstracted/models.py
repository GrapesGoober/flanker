from dataclasses import dataclass

from flanker_core.gamestate import GameState
from flanker_core.models.outcomes import AssaultOutcomes, FireOutcomes
from flanker_core.models.vec2 import Vec2


@dataclass
class MoveAction:
    unit_id: int
    to: Vec2


@dataclass
class FireAction:
    unit_id: int
    target_id: int


@dataclass
class AssaultAction:
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


Action = MoveAction | FireAction | AssaultAction
ActionResult = MoveActionResult | FireActionResult | AssaultActionResult
