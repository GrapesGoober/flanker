from copy import deepcopy
from dataclasses import dataclass

from flanker_ai.config_models import (
    PolicyConfig,
    SearchPolicyConfig,
    UnabstractedStateConfig,
    WaypointsStateConfig,
)
from flanker_ai.search_policies.expectimax_policy import ExpectimaxPolicy
from flanker_ai.search_policies.mcts_policy import MctsPolicy, MctsTreeNode
from flanker_ai.search_policies.minimax_policy import MinimaxPolicy
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
        search_log: "AiSearchAgent.AiSearchLog"

    @dataclass
    class GameTreeNode:
        state: GameState
        children: list[tuple[Action, "AiSearchAgent.GameTreeNode"]]

    @dataclass
    class GameTreeResult:
        game_tree: "AiSearchAgent.GameTreeNode"
        best_action: Action

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
    ) -> ActionResult | None:
        """
        Performs an action and return its result.
        Returns `None` if no legal actions possible.
        """

        # Prepare the representation and run the policy on it
        state = AiSearchAgent.get_state(gs, config)
        action: Action | None
        search_log: AiSearchAgent.AiSearchLog
        match config.policy:
            case PolicyConfig.ExpectimaxPolicy():
                action, expectimax_log = ExpectimaxPolicy[Action].get_action(
                    rs=state, depth=config.policy.depth
                )
                search_log = AiSearchAgent.AiSearchLog(
                    tree_size=expectimax_log.tree_size,
                    tree_depth=config.policy.depth,
                )
            case PolicyConfig.MinimaxPolicy():
                action, minimax_log = MinimaxPolicy[Action].get_action(
                    state=state, depth=config.policy.depth
                )
                search_log = AiSearchAgent.AiSearchLog(
                    tree_size=minimax_log.tree_size,
                    tree_depth=config.policy.depth,
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

                action, mcts_log = MctsPolicy[Action].get_action(
                    rs=state,
                    max_iterations=config.policy.max_iterations,
                    max_simulate_length=config.policy.max_simulate_length,
                    simulate_policy=simulate_policy,
                )

                search_log = AiSearchAgent.AiSearchLog(
                    tree_size=config.policy.max_iterations,
                    tree_depth=mcts_log.tree_depth,
                )

        if action == None:
            return None

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

        # Prepare the representation and run the policy on it
        state = AiSearchAgent.get_state(gs, config)
        action: Action | None
        match config.policy:
            case PolicyConfig.ExpectimaxPolicy():
                raise NotImplementedError()
            case PolicyConfig.MinimaxPolicy():
                raise NotImplementedError()
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

                action, mcts_log = MctsPolicy[Action].get_action(
                    rs=state,
                    max_iterations=config.policy.max_iterations,
                    max_simulate_length=config.policy.max_simulate_length,
                    simulate_policy=simulate_policy,
                )

                if action == None:
                    return None

                def map_mcts_tree_to_game_tree(
                    root: MctsTreeNode[Action],
                ) -> AiSearchAgent.GameTreeNode:

                    gs: GameState
                    match root.state:
                        case UnabstractedState() | WaypointsState():
                            gs = root.state.gs
                        case _:
                            raise NotImplementedError()

                    return AiSearchAgent.GameTreeNode(
                        state=gs,
                        children=[
                            (child.action, map_mcts_tree_to_game_tree(child))
                            for child in root.children
                            if child.action != None
                        ],
                    )

                return AiSearchAgent.GameTreeResult(
                    game_tree=map_mcts_tree_to_game_tree(mcts_log.tree_root),
                    best_action=action,
                )

        return None
