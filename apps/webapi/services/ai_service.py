from copy import deepcopy

from flanker_ai.ai_match import AiMatch
from flanker_ai.ai_system import AiActionResult, AiSystem
from flanker_ai.config_models import (
    AiConfigComponent,
    PointsConfig,
    SearchPolicyConfig,
    WaypointsStateConfig,
)
from flanker_ai.search_policies.expectimax_policy import (
    ExpectimaxTreeNode,
)
from flanker_ai.search_policies.mcts_policy import MctsTreeNode
from flanker_ai.search_policies.minimax_policy import MinimaxTreeNode
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
    RallyAction,
    RallyActionResult,
)
from flanker_core.models.components import InitiativeState
from flanker_core.systems.action_system import ActionSystem
from webapi.models.action_models import (
    ActionLogModel,
    ActionModel,
    AssaultActionLogModel,
    AssaultActionModel,
    FireActionLogModel,
    FireActionModel,
    MoveActionLogModel,
    MoveActionModel,
    PivotActionLogModel,
    PivotActionModel,
    RallyActionLogModel,
    RallyActionModel,
)
from webapi.models.inspection_models import (
    ExpectimaxTreeEdgeModel,
    ExpectimaxTreeInspectionModel,
    ExpectimaxTreeNodeModel,
    ExpectimaxTreeOutcomeModel,
    GameTreeInspectionModel,
    MctsTreeEdgeModel,
    MctsTreeInspectionModel,
    MctsTreeNodeModel,
    MinimaxTreeEdgeModel,
    MinimaxTreeInspectionModel,
    MinimaxTreeNodeModel,
)
from webapi.models.state_models import (
    AiActionResultModel,
    AiMatchResponseModel,
    AiSearchLogModel,
    AiWaypointConfigRequestModel,
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

        action_results: list[AiActionResult] = []
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
    ) -> GameTreeInspectionModel | None:
        initiative = ActionSystem.get_initiative(gs)
        tree_result = AiSystem.get_game_tree(gs, faction=initiative)
        if tree_result == None:
            return None

        match tree_result.game_tree:
            case MctsTreeNode():
                return MctsTreeInspectionModel(
                    type="MctsTreeInspectionModel",
                    best_action=AiService._map_action_to_model(
                        tree_result.best_action,
                    ),
                    tree_root=AiService._map_mcts_to_inspection(
                        tree_result.game_tree,
                    ),
                )
            case ExpectimaxTreeNode():
                return ExpectimaxTreeInspectionModel(
                    type="ExpectimaxTreeInspectionModel",
                    best_action=AiService._map_action_to_model(
                        tree_result.best_action,
                    ),
                    tree_root=AiService._map_expectimax_to_inspection(
                        tree_result.game_tree,
                    ),
                )
            case MinimaxTreeNode():
                return MinimaxTreeInspectionModel(
                    type="MinimaxTreeInspectionModel",
                    best_action=AiService._map_action_to_model(
                        tree_result.best_action,
                    ),
                    tree_root=AiService._map_minimax_to_inspection(
                        tree_result.game_tree,
                    ),
                )

    @staticmethod
    def run_match(gs: GameState) -> AiMatchResponseModel:
        """Runs a match where 2 AI agents plays against each other."""
        result = AiMatch.run_match(gs)
        AiService._log_ai_action_results(
            gs=gs,
            results=result.action_results,
            gs_snapshots=result.gs_snapshots,
        )
        return AiMatchResponseModel(
            winner=result.winner,
            total_runtime_seconds=result.total_runtime_seconds,
            action_results=[
                AiActionResultModel(
                    faction=result.faction,
                    action_runtime_seconds=result.action_runtime_seconds,
                    policy_log=(
                        AiSearchLogModel(
                            tree_size=result.policy_log.tree_size,
                            tree_depth=result.policy_log.tree_depth,
                        )
                        if result.policy_log
                        else None
                    ),
                )
                for result in result.action_results
            ],
            json_state=SceneService.serialize(gs),
        )

    @staticmethod
    def set_ai_waypoints_coordinates(
        gs: GameState,
        request: AiWaypointConfigRequestModel,
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
        results: list[AiActionResult],
        gs_snapshots: list[GameState],
    ) -> None:
        for result, gs_snapshot in zip(results, gs_snapshots):
            log = AiService._map_action_result_to_logs(result, gs_snapshot)
            LoggingService.log(gs, log)

    @staticmethod
    def _map_action_to_model(
        action: Action,
    ) -> ActionModel:
        match action:
            case MoveAction():
                return MoveActionModel(
                    action_type="MoveActionModel",
                    unit_id=action.unit_id,
                    to=action.to,
                )
            case PivotAction():
                return PivotActionModel(
                    action_type="PivotActionModel",
                    unit_id=action.unit_id,
                    to=action.to,
                )
            case FireAction():
                return FireActionModel(
                    action_type="FireActionModel",
                    unit_id=action.unit_id,
                    target_id=action.target_id,
                )
            case AssaultAction():
                return AssaultActionModel(
                    action_type="AssaultActionModel",
                    unit_id=action.unit_id,
                    target_id=action.target_id,
                )
            case RallyAction():
                return RallyActionModel(
                    action_type="RallyActionModel",
                    unit_id=action.unit_id,
                )

    @staticmethod
    def _map_action_result_to_logs(
        result: AiActionResult,
        gs_snapshot: GameState,
    ) -> ActionLogModel:
        match result.action, result.result:
            case MoveAction(), MoveActionResult():
                return MoveActionLogModel(
                    body=MoveActionModel(
                        unit_id=result.action.unit_id,
                        to=result.action.to,
                    ),
                    reactive_fire_outcomes=result.result.reactive_fire_outcomes,
                    view_state=GameViewService.get_view_state(gs_snapshot),
                )

            case PivotAction(), PivotActionResult():
                return PivotActionLogModel(
                    body=PivotActionModel(
                        unit_id=result.action.unit_id,
                        to=result.action.to,
                    ),
                    reactive_fire_outcomes=result.result.reactive_fire_outcomes,
                    view_state=GameViewService.get_view_state(gs_snapshot),
                )
            case FireAction(), FireActionResult():
                return FireActionLogModel(
                    body=FireActionModel(
                        unit_id=result.action.unit_id,
                        target_id=result.action.target_id,
                    ),
                    outcome=result.result.outcome,
                    view_state=GameViewService.get_view_state(gs_snapshot),
                )
            case AssaultAction(), AssaultActionResult():
                return AssaultActionLogModel(
                    body=AssaultActionModel(
                        unit_id=result.action.unit_id,
                        target_id=result.action.target_id,
                    ),
                    outcome=result.result.outcome,
                    reactive_fire_outcomes=result.result.reactive_fire_outcomes,
                    view_state=GameViewService.get_view_state(gs_snapshot),
                )
            case RallyAction(), RallyActionResult():
                return RallyActionLogModel(
                    body=RallyActionModel(
                        unit_id=result.action.unit_id,
                    ),
                    view_state=GameViewService.get_view_state(gs_snapshot),
                )

            case _:
                raise ValueError(f"Unknown type {result=}")

    @staticmethod
    def _map_mcts_to_inspection(
        node: MctsTreeNode[Action],
    ) -> MctsTreeNodeModel:
        return MctsTreeNodeModel(
            view_state=GameViewService.get_view_state(
                node.state.get_game_state_copy(),
            ),
            children=[
                MctsTreeEdgeModel(
                    action=AiService._map_action_to_model(child.action),
                    node=AiService._map_mcts_to_inspection(child),
                )
                for child in node.children
                if child.action is not None
            ],
            total_visits=node.total_visits,
            total_value=node.total_value,
        )

    @staticmethod
    def _map_minimax_to_inspection(
        node: MinimaxTreeNode[Action],
    ) -> MinimaxTreeNodeModel:
        return MinimaxTreeNodeModel(
            view_state=GameViewService.get_view_state(
                node.state.get_game_state_copy(),
            ),
            children=[
                MinimaxTreeEdgeModel(
                    action=AiService._map_action_to_model(edge.action),
                    node=AiService._map_minimax_to_inspection(edge.node),
                    best_score=edge.best_score,
                )
                for edge in node.children
            ],
        )

    @staticmethod
    def _map_expectimax_to_inspection(
        node: ExpectimaxTreeNode[Action],
    ) -> ExpectimaxTreeNodeModel:
        return ExpectimaxTreeNodeModel(
            view_state=GameViewService.get_view_state(
                node.state.get_game_state_copy(),
            ),
            children=[
                ExpectimaxTreeEdgeModel(
                    action=AiService._map_action_to_model(edge.action),
                    outcomes=[
                        ExpectimaxTreeOutcomeModel(
                            probability=outcome.probability,
                            node=AiService._map_expectimax_to_inspection(
                                outcome.node,
                            ),
                            score=outcome.score,
                        )
                        for outcome in edge.outcomes
                    ],
                    expected_score=edge.expected_score,
                )
                for edge in node.children
            ],
        )
