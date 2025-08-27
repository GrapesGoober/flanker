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
    def move(gs: GameState, body: MoveActionRequest) -> None:
        """Move a unit and trigger AI response for the opponent."""
        result = MoveSystem.move(gs, body.unit_id, body.to)
        LoggingService.log(
            MoveActionLog(
                body=body,
                result=result,
                unit_state=CombatUnitService.get_units(gs),
            )
        )

    @staticmethod
    def fire(gs: GameState, body: FireActionRequest) -> None:
        """Perform fire action and trigger AI response for the opponent."""
        result = FireSystem.fire(gs, body.unit_id, body.target_id)
        LoggingService.log(
            FireActionLog(
                body=body,
                result=result,
                unit_state=CombatUnitService.get_units(gs),
            )
        )

    @staticmethod
    def assault(gs: GameState, body: AssaultActionRequest) -> None:
        """Perform fire action and trigger AI response for the opponent."""
        result = AssaultSystem.assault(gs, body.unit_id, body.target_id)
        LoggingService.log(
            AssaultActionLog(
                body=body,
                result=result,
                unit_state=CombatUnitService.get_units(gs),
            )
        )

    @staticmethod
    def perform_action(
        gs: GameState,
        body: MoveActionRequest | FireActionRequest | AssaultActionRequest,
    ) -> None:
        if isinstance(body, MoveActionRequest):
            ActionService.move(gs, body)
        elif isinstance(body, FireActionRequest):
            ActionService.fire(gs, body)
        else:
            ActionService.assault(gs, body)
