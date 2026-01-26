from flanker_ai.minimax_player import MinimaxPlayer
from flanker_ai.models import AssaultActionResult, FireActionResult, MoveActionResult

from core.gamestate import GameState
from core.models.components import InitiativeState
from core.systems.initiative_system import InitiativeSystem
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


class AiService:
    """Provides static methods for basic AI behavior."""

    @staticmethod
    def play(gs: GameState) -> None:
        """Not implemented. This REDFOR AI will just pass initiative."""
        # Assume that the AI plays RED
        faction = InitiativeState.Faction.RED
        if InitiativeSystem.get_initiative(gs) != faction:
            return

        # For now, pass on initiative without any actions
        InitiativeSystem.flip_initiative(gs)

    @staticmethod
    def play_minimax(gs: GameState, depth: int) -> None:
        """Runs a minimax search AI for a given game's BLUEFOR faction."""

        _, results = MinimaxPlayer.play_minimax(gs, depth)
        LoggingService.clear_logs(gs)
        for result in results:
            match result:
                case MoveActionResult():
                    log = MoveActionLog(
                        body=MoveActionRequest(
                            unit_id=result.action.unit_id,
                            to=result.action.to,
                        ),
                        reactive_fire_outcome=result.reactive_fire_outcome,
                        unit_state=CombatUnitService.get_units_view_state(
                            result.result_gs
                        ),
                    )
                case FireActionResult():
                    log = FireActionLog(
                        body=FireActionRequest(
                            unit_id=result.action.unit_id,
                            target_id=result.action.target_id,
                        ),
                        outcome=result.outcome,
                        unit_state=CombatUnitService.get_units_view_state(
                            result.result_gs
                        ),
                    )
                case AssaultActionResult():
                    log = AssaultActionLog(
                        body=AssaultActionRequest(
                            unit_id=result.action.unit_id,
                            target_id=result.action.target_id,
                        ),
                        outcome=result.outcome,
                        unit_state=CombatUnitService.get_units_view_state(
                            result.result_gs
                        ),
                    )

            LoggingService.log(gs, log)
