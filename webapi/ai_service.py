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
from flanker_core.models.outcomes import InvalidAction
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
    def play_redfor(gs: GameState) -> None:
        """Runs the default REDFOR AI."""
        AI_FACTION = InitiativeState.Faction.RED
        if InitiativeSystem.get_initiative(gs) != AI_FACTION:
            return
        waypoints_gs = WaypointScheme.create_grid_waypoints(gs, spacing=20, offset=10)
        WaypointScheme.add_combat_units(waypoints_gs, gs, 10)
        halt_counter = 0
        while InitiativeSystem.get_initiative(gs) == AI_FACTION:
            # Runs the abstracted graph search
            _, waypoint_actions = WaypointsMinimaxPlayer.play(waypoints_gs, depth=4)
            current_action = waypoint_actions[0]
            result = WaypointScheme.apply_action(gs, waypoints_gs, current_action)
            if isinstance(result, InvalidAction):
                InitiativeSystem.flip_initiative(gs)
                break
            if halt_counter > 20:
                InitiativeSystem.flip_initiative(gs)
                print("AI is making too many useless actions, breaking")
            assert isinstance(result, ActionResult)
            AiService._log_ai_action_results(gs, [result])
            halt_counter += 1

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
        (prototype) Runs a minimax search and logs
        sequential results for BLUEFOR faction.
        """

        _, results = TreeSearchPlayer.play_minimax(gs, depth)
        LoggingService.clear_logs(gs)
        AiService._log_ai_action_results(gs, results)
