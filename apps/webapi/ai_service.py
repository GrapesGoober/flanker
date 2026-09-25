from copy import deepcopy

from flanker_ai.ai_action_result import AiActionResult
from flanker_ai.ai_match import AiMatch
from flanker_ai.ai_random_heuristic_agent import RandomHeuristicLog
from flanker_ai.ai_system import AiSystem
from flanker_ai.config_models import (
    AiConfigComponent,
    PointsConfig,
    SearchPolicyConfig,
    WaypointsStateConfig,
)
from flanker_ai.policies.search_log_models import AiSearchLog
from flanker_core.gamestate import GameState
from flanker_core.models.actions import (
    AssaultAction,
    AssaultActionResult,
    FireAction,
    FireActionResult,
    MoveAction,
    MoveActionResult,
    PivotAction,
    PivotActionResult,
)
from flanker_core.models.components import InitiativeState
from flanker_core.systems.initiative_system import InitiativeSystem
from webapi.logging_service import LoggingService
from webapi.models import (
    AiMatchResponse,
    AiWaypointConfigRequest,
    AssaultActionLog,
    AssaultActionRequest,
    FireActionLog,
    FireActionRequest,
    MoveActionLog,
    MoveActionRequest,
    PivotActionLog,
    PivotActionRequest,
)
from webapi.scene_service import SceneService


class AiService:
    """Provides static methods for basic AI behavior."""

    @staticmethod
    def play_red_initiative(
        gs: GameState,
        max_actions: int = 10,
    ) -> None:
        """Runs the default RED AI for entire RED initiative."""
        if InitiativeSystem.get_initiative(gs) != InitiativeState.Faction.RED:
            return

        action_results: list[
            AiActionResult[AiSearchLog] | AiActionResult[RandomHeuristicLog]
        ] = []
        gs_snapshots: list[GameState] = []
        for _ in range(max_actions):

            result = AiSystem.perform_action(
                gs=gs,
                faction=InitiativeSystem.get_initiative(gs),
            )

            if result == None:
                InitiativeSystem.flip_initiative(gs)
                break
            action_results.append(result)
            gs_snapshots.append(deepcopy(gs))

        action_results = [action_result for action_result in action_results]
        AiService._log_ai_action_results(
            gs=gs,
            results=action_results,
            gs_snapshots=gs_snapshots,
        )

    @staticmethod
    def run_match(gs: GameState) -> AiMatchResponse:
        """Runs a match where 2 AI agents plays against each other."""
        result = AiMatch.run_match(gs)
        AiService._log_ai_action_results(
            gs=gs,
            results=result.action_results,
            gs_snapshots=result.gs_snapshots,
        )
        return AiMatchResponse(
            winner=result.winner,
            total_runtime_seconds=result.total_runtime_seconds,
            action_results=result.action_results,
            json_state=SceneService.serialize(gs),
        )

    @staticmethod
    def set_ai_waypoints_coordinates(
        gs: GameState,
        request: AiWaypointConfigRequest,
    ) -> None:
        for _, config_component in gs.query(AiConfigComponent):
            if config_component.faction != request.faction:
                continue
            if not isinstance(config_component.config, SearchPolicyConfig):
                continue
            if not isinstance(config_component.config.state, WaypointsStateConfig):
                continue
            points_config = config_component.config.state.waypoints
            if not isinstance(points_config, PointsConfig.HandDrawn):
                continue
            points_config.points = request.points

    @staticmethod
    def _log_ai_action_results(
        gs: GameState,
        results: list[AiActionResult[AiSearchLog] | AiActionResult[RandomHeuristicLog]],
        gs_snapshots: list[GameState],
    ) -> None:
        for result, gs_snapshot in zip(results, gs_snapshots):
            match result.action, result.result:
                case MoveAction(), MoveActionResult():
                    log = MoveActionLog(
                        body=MoveActionRequest(
                            unit_id=result.action.unit_id,
                            to=result.action.to,
                        ),
                        reactive_fire_outcomes=result.result.reactive_fire_outcomes,
                        view_state=SceneService.get_view_state(gs_snapshot),
                    )

                case PivotAction(), PivotActionResult():
                    log = PivotActionLog(
                        body=PivotActionRequest(
                            unit_id=result.action.unit_id,
                            to=result.action.to,
                        ),
                        reactive_fire_outcomes=result.result.reactive_fire_outcomes,
                        view_state=SceneService.get_view_state(gs_snapshot),
                    )
                case FireAction(), FireActionResult():
                    log = FireActionLog(
                        body=FireActionRequest(
                            unit_id=result.action.unit_id,
                            target_id=result.action.target_id,
                        ),
                        outcome=result.result.outcome,
                        view_state=SceneService.get_view_state(gs_snapshot),
                    )
                case AssaultAction(), AssaultActionResult():
                    log = AssaultActionLog(
                        body=AssaultActionRequest(
                            unit_id=result.action.unit_id,
                            target_id=result.action.target_id,
                        ),
                        outcome=result.result.outcome,
                        reactive_fire_outcomes=result.result.reactive_fire_outcomes,
                        view_state=SceneService.get_view_state(gs_snapshot),
                    )

                case _:
                    raise ValueError(f"Unknown type {result=}")

            LoggingService.log(gs, log)
