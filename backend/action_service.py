from fastapi import HTTPException, status
from backend.models import FireActionRequest, MoveActionRequest
from core.faction_system import FactionSystem
from core.fire_system import FireSystem
from core.gamestate import GameState
from core.move_system import MoveSystem


class ActionService:
    """Provides static methods to process player actions."""

    @staticmethod
    def _verify_faction(gs: GameState, unit_id: int, faction_id: int) -> None:
        if FactionSystem.get_faction_id(gs, unit_id) != faction_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unit {unit_id} is not part of player faction",
            )

    @staticmethod
    def move(
        gs: GameState,
        body: MoveActionRequest,
        player_faction_id: int,
    ) -> None:
        """Move a unit and trigger AI response for the opponent."""
        ActionService._verify_faction(gs, body.unit_id, player_faction_id)
        MoveSystem.move(gs, body.unit_id, body.to)

    @staticmethod
    def fire(
        gs: GameState,
        body: FireActionRequest,
        player_faction_id: int,
    ) -> None:
        """Perform fire action and trigger AI response for the opponent."""
        ActionService._verify_faction(gs, body.unit_id, player_faction_id)
        FireSystem.fire(gs, body.unit_id, body.target_id)
