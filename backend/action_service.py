from backend.combat_unit_service import CombatUnitService
from backend.log_models import AssaultActionLog, FireActionLog, MoveActionLog
from backend.logging_service import LoggingService
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
    def move(gs: GameState, body: MoveActionRequest) -> bool:
        """Move a unit and trigger AI response for the opponent."""
        result = MoveSystem.move(gs, body.unit_id, body.to)
        LoggingService.log(
            MoveActionLog(
                body=body,
                result=result,
                unit_state=CombatUnitService.get_units(gs),
            )
        )
        return result.is_valid

    @staticmethod
    def fire(gs: GameState, body: FireActionRequest) -> bool:
        """Perform fire action and trigger AI response for the opponent."""
        result = FireSystem.fire(gs, body.unit_id, body.target_id)
        LoggingService.log(
            FireActionLog(
                body=body,
                result=result,
                unit_state=CombatUnitService.get_units(gs),
            )
        )
        return result.is_valid

    @staticmethod
    def assault(gs: GameState, body: AssaultActionRequest) -> bool:
        """Perform fire action and trigger AI response for the opponent."""
        result = AssaultSystem.assault(gs, body.unit_id, body.target_id)
        LoggingService.log(
            AssaultActionLog(
                body=body,
                result=result,
                unit_state=CombatUnitService.get_units(gs),
            )
        )
        return result.is_valid

    @staticmethod
    def perform_action(
        gs: GameState,
        body: MoveActionRequest | FireActionRequest | AssaultActionRequest,
    ) -> bool:
        if isinstance(body, MoveActionRequest):
            result = ActionService.move(gs, body)
        elif isinstance(body, FireActionRequest):
            result = ActionService.fire(gs, body)
        else:
            result = ActionService.assault(gs, body)
        return result
