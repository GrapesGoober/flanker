from backend.models import FireActionRequest, MoveActionRequest
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
