from backend.models import (
    AssaultActionRequest,
    FireActionRequest,
    MoveActionRequest,
)
from core.assault_system import AssaultSystem
from core.fire_system import FireSystem
from core.gamestate import GameState
from core.move_system import MoveSystem


class ActionService:
    """Provides static methods to process player actions."""

    @staticmethod
    def move(gs: GameState, body: MoveActionRequest) -> None:
        """Move a unit and trigger AI response for the opponent."""
        MoveSystem.move(gs, body.unit_id, body.to)

    @staticmethod
    def fire(gs: GameState, body: FireActionRequest) -> None:
        """Perform fire action and trigger AI response for the opponent."""
        FireSystem.fire(gs, body.unit_id, body.target_id)

    @staticmethod
    def assault(gs: GameState, body: AssaultActionRequest) -> None:
        """Perform fire action and trigger AI response for the opponent."""
        AssaultSystem.assault(gs, body.unit_id, body.target_id)
