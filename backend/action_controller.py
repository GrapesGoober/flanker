from fastapi import HTTPException, status
from backend.basic_ai_controller import BasicAiController
from backend.models import MoveActionRequest
from backend.squad_controller import UnitState, UnitStateController
from core.command import Command
from core.gamestate import GameState
from core.move_action import MoveAction


class ActionController:

    @staticmethod
    def move(
        gs: GameState,
        body: MoveActionRequest,
        player_faction_id: int,
        opponent_faction_id: int,
    ) -> UnitState:
        if Command.get_faction_id(gs, body.unit_id) != player_faction_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unit {body.unit_id} is not part of player faction",
            )
        MoveAction.move(gs, body.unit_id, body.to)
        BasicAiController.play(gs, opponent_faction_id)
        return UnitStateController.get_unit_state(gs, player_faction_id)
