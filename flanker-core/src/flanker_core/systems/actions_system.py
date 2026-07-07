from uuid import UUID

from flanker_core.gamestate import GameState
from flanker_core.models.actions import (
    MoveAction,
    MoveActionResult,
    PivotAction,
    PivotActionResult,
)
from flanker_core.models.outcomes import InvalidAction
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.move_system import MoveSystem


class ActionsSystem:
    """Static system class to perform all in-game actions."""

    @staticmethod
    def perform(
        gs: GameState,
        action: MoveAction | PivotAction,
    ) -> PivotActionResult | MoveActionResult | InvalidAction:
        match action:
            case MoveAction():
                return MoveSystem.move(gs, action.unit_id, action.to)
            case PivotAction():
                return MoveSystem.pivot(gs, action.unit_id, action.to)

    @staticmethod
    def pivot(
        gs: GameState,
        unit_id: UUID,
        to: Vec2,
    ) -> PivotActionResult | InvalidAction:
        return MoveSystem.pivot(gs, unit_id, to)

    @staticmethod
    def fire(): ...

    @staticmethod
    def assault(): ...
