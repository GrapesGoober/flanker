from flanker_ai.ai_config_manager import AiConfigManager
from flanker_ai.unabstracted.models import (
    ActionResult,
    AssaultActionResult,
    FireActionResult,
    MoveActionResult,
)
from flanker_ai.unabstracted.tree_search_player import TreeSearchPlayer
from flanker_core.gamestate import GameState
from flanker_core.models.components import InitiativeState

from webapi.combat_unit_service import CombatUnitService
from webapi.logging_service import LoggingService
from webapi.models import (
    AiWaypointConfigRequest,
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
    def play_redfor(gs: GameState) -> None:
        """Runs the default REDFOR AI."""

        player = AiConfigManager.get_player(gs, InitiativeState.Faction.RED)

        results = player.play_initiative()

        AiService._log_ai_action_results(gs, results)

    @staticmethod
    def play_minimax(gs: GameState, depth: int) -> None:
        """
        (prototype) Runs an unabstracted minimax search and logs
        sequential results for a BLUE faction.
        """

        _, results = TreeSearchPlayer.play_minimax(gs, depth)
        LoggingService.clear_logs(gs)
        AiService._log_ai_action_results(gs, results)

    @staticmethod
    def update_ai_config(
        gs: GameState,
        request: AiWaypointConfigRequest,
    ) -> None:
        config = AiConfigManager.get_ai_config(gs, request.faction)
        config.waypoint_coordinates = request.points

    @staticmethod
    def _log_ai_action_results(
        gs: GameState,
        results: list[ActionResult],
    ) -> None:
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
                case _:
                    raise ValueError(f"Unknown type {result=}")

            LoggingService.log(gs, log)
