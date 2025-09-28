from backend.combat_unit_service import CombatUnitService
from backend.log_models import AssaultActionLog, FireActionLog, MoveActionLog
from backend.logging_service import LoggingService
from backend.models import (
    AssaultActionRequest,
    FireActionRequest,
    MoveActionRequest,
)
from core.action_models import AssaultAction, FireAction, MoveAction
from core.systems.assault_system import AssaultSystem
from core.systems.fire_system import FireSystem
from core.systems.move_system import MoveSystem
from core.gamestate import GameState


class ActionService:
    """Provides static methods to process player actions."""

    @staticmethod
    def move(gs: GameState, body: MoveActionRequest) -> bool:
        """Move a unit and trigger AI response for the opponent."""
        result = MoveSystem.move(gs, MoveAction(body.unit_id, body.to))
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
        result = FireSystem.fire(gs, FireAction(body.unit_id, body.target_id))
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
        result = AssaultSystem.assault(gs, AssaultAction(body.unit_id, body.target_id))
        LoggingService.log(
            AssaultActionLog(
                body=body,
                result=result,
                unit_state=CombatUnitService.get_units(gs),
            )
        )
        return result.is_valid
