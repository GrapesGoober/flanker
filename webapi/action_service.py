from fastapi import HTTPException, status
from flanker_core.gamestate import GameState
from flanker_core.models.actions import (
    AssaultAction,
    FireAction,
    MoveAction,
    PivotAction,
)
from flanker_core.models.outcomes import InvalidAction
from flanker_core.systems.actions_system import ActionsSystem

from webapi.combat_unit_service import CombatUnitService
from webapi.logging_service import LoggingService
from webapi.models import (
    AssaultActionLog,
    AssaultActionRequest,
    FireActionLog,
    FireActionRequest,
    MoveActionLog,
    MoveActionRequest,
    PivotActionLog,
    PivotActionRequest,
)


class ActionService:
    """Provides static methods to process player actions."""

    @staticmethod
    def move(gs: GameState, body: MoveActionRequest) -> None:
        """Perform a move action."""
        result = ActionsSystem.perform(gs, MoveAction(body.unit_id, body.to))
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
    def pivot(gs: GameState, body: PivotActionRequest) -> None:
        """Perform a pivot action."""
        result = ActionsSystem.perform(gs, PivotAction(body.unit_id, body.to))
        if isinstance(result, InvalidAction):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=result)
        LoggingService.log(
            gs,
            PivotActionLog(
                body=body,
                reactive_fire_outcome=result.reactive_fire_outcome,
                unit_state=CombatUnitService.get_units_view_state(gs),
            ),
        )

    @staticmethod
    def fire(gs: GameState, body: FireActionRequest) -> None:
        """Perform a fire action."""

        result = ActionsSystem.perform(
            gs=gs,
            action=FireAction(
                unit_id=body.unit_id,
                target_id=body.target_id,
            ),
        )
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
        """Perform an assault action."""
        result = ActionsSystem.perform(
            gs=gs,
            action=AssaultAction(
                unit_id=body.unit_id,
                target_id=body.target_id,
            ),
        )
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
