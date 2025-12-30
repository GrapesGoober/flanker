from fastapi import HTTPException, status
from backend.combat_unit_service import CombatUnitService
from backend.models import (
    AssaultActionLog,
    FireActionLog,
    MoveActionLog,
    MoveActionResult,
)
from backend.logging_service import LoggingService
from backend.models import (
    AssaultActionRequest,
    FireActionRequest,
    MoveActionRequest,
)
from core.action_models import AssaultAction, InvalidActionTypes
from core.systems.assault_system import AssaultSystem
from core.systems.fire_system import FireSystem
from core.systems.move_system import MoveSystem
from core.gamestate import GameState


class ActionService:
    """Provides static methods to process player actions."""

    @staticmethod
    def move(gs: GameState, body: MoveActionRequest) -> None:
        """Move a unit and trigger AI response for the opponent."""
        result = MoveSystem.move(gs, body.unit_id, body.to)
        if isinstance(result, InvalidActionTypes):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=result)
        LoggingService.log(
            gs,
            MoveActionLog(
                body=body,
                result=MoveActionResult(
                    reactive_fire_outcome=result.reactive_fire_outcome
                ),
                unit_state=CombatUnitService.get_units(gs),
            ),
        )

    @staticmethod
    def fire(gs: GameState, body: FireActionRequest) -> None:
        """Perform fire action and trigger AI response for the opponent."""
        result = FireSystem.fire(gs, body.unit_id, body.target_id)
        if isinstance(result, InvalidActionTypes):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=result)
        LoggingService.log(
            gs,
            FireActionLog(
                body=body,
                result=result,
                unit_state=CombatUnitService.get_units(gs),
            ),
        )

    @staticmethod
    def assault(gs: GameState, body: AssaultActionRequest) -> None:
        """Perform fire action and trigger AI response for the opponent."""
        result = AssaultSystem.assault(gs, AssaultAction(body.unit_id, body.target_id))
        if isinstance(result, InvalidActionTypes):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=result)
        LoggingService.log(
            gs,
            AssaultActionLog(
                body=body,
                result=result,
                unit_state=CombatUnitService.get_units(gs),
            ),
        )
