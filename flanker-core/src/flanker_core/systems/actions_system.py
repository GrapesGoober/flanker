from uuid import UUID

from flanker_core.gamestate import GameState
from flanker_core.models.outcomes import (
    InvalidAction,
    MoveActionResult,
)
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.move_system import MoveSystem


class ActionsSystem:
    """Static system class to perform all in-game actions."""

    @staticmethod
    def move(
        gs: GameState,
        unit_id: UUID,
        to: Vec2,
    ) -> MoveActionResult | InvalidAction:
        return MoveSystem.move(gs, unit_id, to)

    @staticmethod
    def pivot(): ...

    @staticmethod
    def fire(): ...

    @staticmethod
    def assault(): ...
