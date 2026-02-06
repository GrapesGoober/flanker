from dataclasses import dataclass

from flanker_ai.unabstracted.models import (
    ActionResult,
    AssaultActionResult,
    FireActionResult,
    MoveActionResult,
)
from flanker_ai.unabstracted.tree_search_player import TreeSearchPlayer
from flanker_ai.waypoints.models import WaypointAction
from flanker_ai.waypoints.waypoints_minimax_player import WaypointsMinimaxPlayer
from flanker_core.gamestate import GameState
from flanker_core.models.components import InitiativeState

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


@dataclass
class _AiPlayer:
    player: WaypointsMinimaxPlayer


class AiService:
    """Provides static methods for basic AI behavior."""

    @staticmethod
    def play_redfor(gs: GameState) -> None:
        """Runs the default REDFOR AI."""
        if results := gs.query(_AiPlayer):
            _, player_component = results[0]
            player = player_component.player
        else:
            player = WaypointsMinimaxPlayer(
                gs=gs,
                faction=InitiativeState.Faction.RED,
                search_depth=4,
                grid_spacing=20,
                grid_offset=10,
            )
            gs.add_entity(_AiPlayer(player))

        def log_results(result: ActionResult) -> None:
            result_gs = result.result_gs
            AiService._log_ai_action_results(result_gs, [result])

        def print_actions_sequence(actions: list[WaypointAction]) -> None:
            print(f"Action sequences {actions}")

        results = player.play_initiative(
            action_callback=log_results,
            sequence_callback=print_actions_sequence,
        )

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

    @staticmethod
    def play_minimax(gs: GameState, depth: int) -> None:
        """
        (prototype) Runs an unabstracted minimax search and logs
        sequential results for a BLUE faction.
        """

        _, results = TreeSearchPlayer.play_minimax(gs, depth)
        LoggingService.clear_logs(gs)
        AiService._log_ai_action_results(gs, results)
