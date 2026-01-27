from fastapi import HTTPException, status
from flanker_core.gamestate import GameState
from flanker_core.models.outcomes import InvalidAction
from flanker_core.systems.assault_system import AssaultSystem
from flanker_core.systems.fire_system import FireSystem
from flanker_core.systems.move_system import MoveSystem

from webapi.combat_unit_service import CombatUnitService
from webapi.logging_service import LoggingService
from webapi.models import (
    AssaultActionLog,
    AssaultActionRequest,
    FireActionLog,
    FireActionRequest,
    MoveActionLog,
    MoveActionRequest,
)


class ActionService:
    """Provides static methods to process player actions."""

    @staticmethod
    def move(gs: GameState, body: MoveActionRequest) -> None:
        """Move a unit and trigger AI response for the opponent."""
        result = MoveSystem.move(gs, body.unit_id, body.to)
        if isinstance(result, InvalidAction):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=result)
        LoggingService.log(
            gs,
            MoveActionLog(
                body=body,
                reactive_fire_outcome=result.reactive_fire_outcome,
                unit_state=CombatUnitService.get_units_view_state(gs),
            ),
        )

    @staticmethod
    def fire(gs: GameState, body: FireActionRequest) -> None:
        """Perform fire action and trigger AI response for the opponent."""
        result = FireSystem.fire(gs, body.unit_id, body.target_id)
        if isinstance(result, InvalidAction):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=result)
        LoggingService.log(
            gs,
            FireActionLog(
                body=body,
                outcome=result.outcome,
                unit_state=CombatUnitService.get_units_view_state(gs),
            ),
        )

    @staticmethod
    def assault(gs: GameState, body: AssaultActionRequest) -> None:
        """Perform fire action and trigger AI response for the opponent."""
        result = AssaultSystem.assault(gs, body.unit_id, body.target_id)
        if isinstance(result, InvalidAction):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=result)
        LoggingService.log(
            gs,
            AssaultActionLog(
                body=body,
                outcome=result.outcome,
                reactive_fire_outcome=result.reactive_fire_outcome,
                unit_state=CombatUnitService.get_units_view_state(gs),
            ),
        )
