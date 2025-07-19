from fastapi import HTTPException, status
from backend.basic_ai_controller import BasicAiController
from backend.models import MoveActionRequest
from core.faction_system import FactionSystem
from core.gamestate import GameState
from core.move_system import MoveSystem


class ActionController:
    """Provides static methods to process player actions."""

    @staticmethod
    def move(
        gs: GameState,
        body: MoveActionRequest,
        player_faction_id: int,
        opponent_faction_id: int,
    ) -> None:
        """Move a unit and trigger AI response for the opponent."""
        if FactionSystem.get_faction_id(gs, body.unit_id) != player_faction_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unit {body.unit_id} is not part of player faction",
            )
        MoveSystem.move(gs, body.unit_id, body.to)
        BasicAiController.play(gs, opponent_faction_id)
