from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

from flanker_ai.config_models import (
    PolicyConfig,
    SearchPolicyConfig,
    UnabstractedStateConfig,
    WaypointsStateConfig,
)
from flanker_ai.search_policies.expectimax_policy import (
    ExpectimaxPolicy,
    ExpectimaxSearchLog,
    ExpectimaxTreeNode,
)
from flanker_ai.search_policies.mcts_policy import (
    MctsPolicy,
    MctsSearchLog,
    MctsTreeNode,
)
from flanker_ai.search_policies.minimax_policy import (
    MinimaxPolicy,
    MinimaxSearchLog,
    MinimaxTreeNode,
)
from flanker_ai.search_policies.random_heuristic_policy import RandomHeuristicPolicy
from flanker_ai.search_policies.random_policy import RandomPolicy
from flanker_ai.search_states.i_search_state import ISearchState
from flanker_ai.search_states.unabstracted.unabstracted_state import UnabstractedState
from flanker_ai.search_states.waypoints.waypoints_state import WaypointsState
from flanker_core.gamestate import GameState
from flanker_core.models.actions import Action, ActionResult
from flanker_core.models.outcomes import InvalidAction
from flanker_core.systems.action_system import ActionSystem


class AiSearchAgent:

    @dataclass
    class AiSearchLog:
        tree_size: int
        tree_depth: int

    @dataclass
    class ActionResult:
        action: Action
        result: ActionResult
        search_log: AiSearchAgent.AiSearchLog

    @dataclass
    class MctsTreeEdge:
        action: Action
        node: AiSearchAgent.MctsTreeNode

    @dataclass
    class MctsTreeNode:
        state: GameState
        children: list[AiSearchAgent.MctsTreeEdge]
        total_visits: int
        total_value: float

    @dataclass
    class MinimaxTreeNode:
        state: GameState
        children: list[AiSearchAgent.MinimaxTreeEdge]

    @dataclass
    class MinimaxTreeEdge:
        action: Action
        node: AiSearchAgent.MinimaxTreeNode
        best_score: float

    @dataclass
    class ExpectimaxTreeOutcome:
        probability: float
        node: AiSearchAgent.ExpectimaxTreeNode

    @dataclass
    class ExpectimaxTreeNode:
        state: GameState
        children: list[AiSearchAgent.ExpectimaxTreeEdge]

    @dataclass
    class ExpectimaxTreeEdge:
        action: Action
        outcomes: list[AiSearchAgent.ExpectimaxTreeOutcome]
        best_score: float

    @dataclass
    class GameTreeResult:
        game_tree: (
            AiSearchAgent.MctsTreeNode
            | AiSearchAgent.MinimaxTreeNode
            | AiSearchAgent.ExpectimaxTreeNode
        )
        best_action: Action

    type _PolicySearchLogs = (
        ExpectimaxSearchLog[Action] | MinimaxSearchLog[Action] | MctsSearchLog[Action]
    )

    @staticmethod
    def get_state(
        gs: GameState,
        config: SearchPolicyConfig,
    ) -> ISearchState[Action]:

        match config.state:
            case UnabstractedStateConfig():
                # The unabstracted state uses lazy move candidate filtering
                state_config = config.state
                state = UnabstractedState(
                    move_pool_config=state_config.move_candidates_pool,
                    move_filter_config=state_config.move_candidates_filter,
                    transposition_schemes=state_config.transposition_schemes,
                )
            case WaypointsStateConfig():
                state_config = config.state
                state = WaypointsState(
                    waypoints_config=state_config.waypoints,
                    move_filter_config=state_config.move_candidates_filter,
                    path_tolerance=state_config.path_tolerance,
                )
        state.update_state(gs)
        return state

    @staticmethod
    def perform_action(
        gs: GameState,
        config: SearchPolicyConfig,
    ) -> AiSearchAgent.ActionResult | None:
        """
        Performs an action and return its result.
        Returns `None` if no legal actions possible.
        """

        state = AiSearchAgent.get_state(gs, config)
        action, log = AiSearchAgent._get_action(state, config)

        if action == None:
            return None

        search_log: AiSearchAgent.AiSearchLog
        match (config.policy, log):
            case PolicyConfig.ExpectimaxPolicy(), ExpectimaxSearchLog():
                search_log = AiSearchAgent.AiSearchLog(
                    tree_size=log.tree_size,
                    tree_depth=config.policy.depth,
                )
            case PolicyConfig.MinimaxPolicy(), MinimaxSearchLog():
                search_log = AiSearchAgent.AiSearchLog(
                    tree_size=log.tree_size,
                    tree_depth=config.policy.depth,
                )
            case PolicyConfig.MctsPolicy(), MctsSearchLog():
                search_log = AiSearchAgent.AiSearchLog(
                    tree_size=config.policy.max_iterations,
                    tree_depth=log.tree_depth,
                )
            case _:
                raise RuntimeError("Policy log is mismatched from config!")

        result = ActionSystem.perform(gs, action)
        if isinstance(result, InvalidAction):
            return None

        # Prevent mutation shenanigans by returning a copy
        return deepcopy(
            AiSearchAgent.ActionResult(
                action=action,
                result=result,
                search_log=search_log,
            )
        )

    @staticmethod
    def get_game_tree(
        gs: GameState,
        config: SearchPolicyConfig,
    ) -> GameTreeResult | None:
        """
        Returns the expanded game tree given the state. This uses the
        AI config of the state. This does not perform the action.
        """

        state = AiSearchAgent.get_state(gs, config)
        action, log = AiSearchAgent._get_action(state, config, log_with_tree=True)

        if action == None:
            return None

        match (config.policy, log):
            case PolicyConfig.ExpectimaxPolicy(), ExpectimaxSearchLog():

                def map_expectimax_model(
                    node: ExpectimaxTreeNode[Action],
                ) -> AiSearchAgent.ExpectimaxTreeNode:
                    gs: GameState
                    match node.state:
                        case UnabstractedState() | WaypointsState():
                            gs = node.state.gs
                        case _:
                            raise NotImplementedError()

                    return AiSearchAgent.ExpectimaxTreeNode(
                        state=gs,
                        children=[
                            AiSearchAgent.ExpectimaxTreeEdge(
                                action=edge.action,
                                outcomes=[
                                    AiSearchAgent.ExpectimaxTreeOutcome(
                                        probability=probability,
                                        node=map_expectimax_model(outcome_node),
                                    )
                                    for probability, outcome_node in edge.outcomes
                                ],
                                best_score=edge.expected_score,
                            )
                            for edge in node.children
                        ],
                    )

                if log.tree_root is None:
                    raise RuntimeError("Expectimax tree logging was not enabled!")

                return AiSearchAgent.GameTreeResult(
                    game_tree=map_expectimax_model(log.tree_root),
                    best_action=action,
                )
            case PolicyConfig.MinimaxPolicy(), MinimaxSearchLog():

                def map_minimax_model(
                    node: MinimaxTreeNode[Action],
                ) -> AiSearchAgent.MinimaxTreeNode:
                    gs: GameState
                    match node.state:
                        case UnabstractedState() | WaypointsState():
                            gs = node.state.gs
                        case _:
                            raise NotImplementedError()

                    return AiSearchAgent.MinimaxTreeNode(
                        state=gs,
                        children=[
                            AiSearchAgent.MinimaxTreeEdge(
                                action=edge.action,
                                node=map_minimax_model(edge.node),
                                best_score=edge.best_score,
                            )
                            for edge in node.children
                        ],
                    )

                if log.tree_root is None:
                    raise RuntimeError("Minimax tree logging was not enabled!")

                return AiSearchAgent.GameTreeResult(
                    game_tree=map_minimax_model(log.tree_root),
                    best_action=action,
                )

            case PolicyConfig.MctsPolicy(), MctsSearchLog():

                def map_mcts_tree_to_game_tree(
                    node: MctsTreeNode[Action],
                ) -> AiSearchAgent.MctsTreeNode:

                    gs: GameState
                    match node.state:
                        case UnabstractedState() | WaypointsState():
                            gs = node.state.gs
                        case _:
                            raise NotImplementedError()

                    return AiSearchAgent.MctsTreeNode(
                        state=gs,
                        children=[
                            AiSearchAgent.MctsTreeEdge(
                                action=child.action,
                                node=map_mcts_tree_to_game_tree(child),
                            )
                            for child in node.children
                            if child.action != None
                        ],
                        total_visits=node.total_visits,
                        total_value=node.total_value,
                    )

                return AiSearchAgent.GameTreeResult(
                    game_tree=map_mcts_tree_to_game_tree(log.tree_root),
                    best_action=action,
                )
            case _:
                raise RuntimeError("Policy log is mismatched from config!")

    @staticmethod
    def _get_action(
        state: ISearchState[Action],
        config: SearchPolicyConfig,
        log_with_tree: bool = False,
    ) -> tuple[Action | None, _PolicySearchLogs]:
        match config.policy:
            case PolicyConfig.ExpectimaxPolicy():
                return ExpectimaxPolicy[Action].get_action(
                    rs=state,
                    depth=config.policy.depth,
                    log_with_tree=log_with_tree,
                )
            case PolicyConfig.MinimaxPolicy():
                return MinimaxPolicy[Action].get_action(
                    state=state,
                    depth=config.policy.depth,
                    log_with_tree=log_with_tree,
                )
            case PolicyConfig.MctsPolicy():
                match config.policy.simulation_policy:
                    case "random":

                        def simulate_policy(rs: ISearchState[Action]) -> Action | None:
                            action, _ = RandomPolicy[Action]().get_action(rs)
                            return action

                    case "rh":

                        def simulate_policy(rs: ISearchState[Action]) -> Action | None:
                            action, _ = RandomHeuristicPolicy().get_action(rs)
                            return action

                return MctsPolicy[Action].get_action(
                    rs=state,
                    max_iterations=config.policy.max_iterations,
                    max_simulate_length=config.policy.max_simulate_length,
                    simulate_policy=simulate_policy,
                )
