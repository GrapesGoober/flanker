from copy import deepcopy

from flanker_ai.agents.ai_search_agent import AiSearchAgent
from flanker_ai.ai_match import AiMatch
from flanker_ai.ai_system import AiSystem
from flanker_ai.config_models import (
    AiConfigComponent,
    PointsConfig,
    SearchPolicyConfig,
    WaypointsStateConfig,
)
from flanker_core.gamestate import GameState
from flanker_core.models.actions import (
    Action,
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
from flanker_core.systems.action_system import ActionSystem
from webapi.models import (
    ActionRequest,
    AiMatchResponse,
    AiWaypointConfigRequest,
    AssaultActionLog,
    AssaultActionRequest,
    FireActionLog,
    FireActionRequest,
    MctsGameTreeInspection,
    MctsGameTreeInspectionNode,
    MoveActionLog,
    MoveActionRequest,
    PivotActionLog,
    PivotActionRequest,
)
from webapi.services.game_view_service import GameViewService
from webapi.services.logging_service import LoggingService
from webapi.services.scene_service import SceneService


class AiService:
    """Provides static methods for basic AI behavior."""

    @staticmethod
    def play_red_initiative(
        gs: GameState,
        max_actions: int = 10,
    ) -> None:
        """Runs the default RED AI for entire RED initiative."""

        action_results: list[AiSystem.ActionResult] = []
        gs_snapshots: list[GameState] = []
        for _ in range(max_actions):
            if ActionSystem.get_initiative(gs) != InitiativeState.Faction.RED:
                break

            result = AiSystem.perform_action(
                gs=gs,
                faction=ActionSystem.get_initiative(gs),
            )

            if result == None:
                ActionSystem.set_initiative(gs, InitiativeState.Faction.BLUE)
                break
            action_results.append(result)
            gs_snapshots.append(deepcopy(gs))

        if action_results != []:
            action_results = [action_result for action_result in action_results]
            AiService._log_ai_action_results(
                gs=gs,
                results=action_results,
                gs_snapshots=gs_snapshots,
            )

    @staticmethod
    def get_tree_inspection(
        gs: GameState,
    ) -> MctsGameTreeInspection | None:
        tree_result = AiSystem.get_game_tree(gs)
        if tree_result == None:
            return None

        def _map_action_model(
            action: Action,
        ) -> ActionRequest:
            match action:
                case MoveAction():
                    return MoveActionRequest(
                        action_type="MoveActionRequest",
                        unit_id=action.unit_id,
                        to=action.to,
                    )
                case PivotAction():
                    return PivotActionRequest(
                        action_type="PivotActionRequest",
                        unit_id=action.unit_id,
                        to=action.to,
                    )
                case FireAction():
                    return FireActionRequest(
                        action_type="FireActionRequest",
                        unit_id=action.unit_id,
                        target_id=action.target_id,
                    )
                case AssaultAction():
                    return AssaultActionRequest(
                        action_type="AssaultActionRequest",
                        unit_id=action.unit_id,
                        target_id=action.target_id,
                    )

        def _map_tree_model(
            tree: AiSearchAgent.GameTreeNode,
        ) -> MctsGameTreeInspectionNode:
            return MctsGameTreeInspectionNode(
                view_state=GameViewService.get_view_state(tree.state),
                children=[
                    (_map_action_model(child_action), _map_tree_model(child_node))
                    for child_action, child_node in tree.children
                ],
            )

        return MctsGameTreeInspection(
            type="MctsGameTreeInspection",
            best_action=_map_action_model(tree_result.best_action),
            tree_root=_map_tree_model(tree_result.game_tree),
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
        results: list[AiSystem.ActionResult],
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
                        view_state=GameViewService.get_view_state(gs_snapshot),
                    )

                case PivotAction(), PivotActionResult():
                    log = PivotActionLog(
                        body=PivotActionRequest(
                            unit_id=result.action.unit_id,
                            to=result.action.to,
                        ),
                        reactive_fire_outcomes=result.result.reactive_fire_outcomes,
                        view_state=GameViewService.get_view_state(gs_snapshot),
                    )
                case FireAction(), FireActionResult():
                    log = FireActionLog(
                        body=FireActionRequest(
                            unit_id=result.action.unit_id,
                            target_id=result.action.target_id,
                        ),
                        outcome=result.result.outcome,
                        view_state=GameViewService.get_view_state(gs_snapshot),
                    )
                case AssaultAction(), AssaultActionResult():
                    log = AssaultActionLog(
                        body=AssaultActionRequest(
                            unit_id=result.action.unit_id,
                            target_id=result.action.target_id,
                        ),
                        outcome=result.result.outcome,
                        reactive_fire_outcomes=result.result.reactive_fire_outcomes,
                        view_state=GameViewService.get_view_state(gs_snapshot),
                    )

                case _:
                    raise ValueError(f"Unknown type {result=}")

            LoggingService.log(gs, log)
