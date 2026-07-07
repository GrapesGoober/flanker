from dataclasses import dataclass

from flanker_core.gamestate import GameState
from flanker_core.models.actions import (
    AssaultAction,
    FireAction,
    MoveAction,
    PivotAction,
)
from flanker_core.models.outcomes import AssaultOutcomes, FireOutcomes


@dataclass
class MoveActionResult:
    action: MoveAction
    result_gs: GameState
    reactive_fire_outcome: FireOutcomes | None = None


@dataclass
class PivotActionResult:
    action: PivotAction
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


Action = MoveAction | PivotAction | FireAction | AssaultAction
ActionResult = (
    MoveActionResult | PivotActionResult | FireActionResult | AssaultActionResult
)
