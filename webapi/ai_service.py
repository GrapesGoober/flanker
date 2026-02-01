from flanker_ai.unabstracted.models import (
    ActionResult,
    AssaultActionResult,
    FireActionResult,
    MoveActionResult,
)
from flanker_ai.unabstracted.tree_search_player import TreeSearchPlayer
from flanker_ai.waypoints.waypoints_minimax_player import WaypointsMinimaxPlayer
from flanker_ai.waypoints.waypoints_scheme import WaypointScheme
from flanker_core.gamestate import GameState
from flanker_core.models.components import InitiativeState
from flanker_core.systems.initiative_system import InitiativeSystem

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
    def _log_ai_action_results(
        gs: GameState,
        results: list[ActionResult],
    ) -> None:
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
                case _:
                    raise ValueError(f"Unknown type {result=}")

            LoggingService.log(gs, log)

    @staticmethod
    def play_minimax(gs: GameState, depth: int) -> None:
        """Runs a minimax search and logs results for BLUEFOR faction."""

        _, results = TreeSearchPlayer.play_minimax(gs, depth)
        AiService._log_ai_action_results(gs, results)

    @staticmethod
    def play_waypointsgraph_minimax(gs: GameState, depth: int) -> None:
        """Runs a waypoint-minimax search and logs results."""
        waypoints_gs = WaypointScheme.create_grid_waypoints(gs, spacing=20, offset=10)
        waypoint_actions = WaypointsMinimaxPlayer.play(waypoints_gs, depth)
        results = WaypointScheme.deabstract_actions(waypoint_actions)
        AiService._log_ai_action_results(gs, results)
