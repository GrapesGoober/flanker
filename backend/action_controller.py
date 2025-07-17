from fastapi import HTTPException, status
from backend.basic_ai_controller import BasicAiController
from backend.models import MoveActionRequest
from core.command import FactionSystem
from core.gamestate import GameState
from core.move_action import MoveActionSystem


class ActionController:

    @staticmethod
    def move(
        gs: GameState,
        body: MoveActionRequest,
        player_faction_id: int,
        opponent_faction_id: int,
    ) -> None:
        if FactionSystem.get_faction_id(gs, body.unit_id) != player_faction_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unit {body.unit_id} is not part of player faction",
            )
        MoveActionSystem.move(gs, body.unit_id, body.to)
        BasicAiController.play(gs, opponent_faction_id)
