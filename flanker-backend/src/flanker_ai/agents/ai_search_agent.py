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


@dataclass
class AiSearchAgentLog:
    tree_size: int
    tree_depth: int


@dataclass
class AiSearchActionResult:
    action: Action
    result: ActionResult
    search_log: AiSearchAgentLog


@dataclass
class AiSearchTreeResult:
    best_action: Action
    game_tree: (
        ExpectimaxTreeNode[Action] | MinimaxTreeNode[Action] | MctsTreeNode[Action]
    )


class AiSearchAgent:

    @staticmethod
    def get_state(
        gs: GameState,
        config: SearchPolicyConfig,
    ) -> ISearchState[Action]:
        """
        Returns an `ISearchState` object initialized to this state and config.
        """

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
    ) -> AiSearchActionResult | None:
        """
        Performs an action and return its result.
        Returns `None` if no legal actions possible.
        """

        state = AiSearchAgent.get_state(gs, config)
        action, log = AiSearchAgent._get_action(state, config)

        if action == None:
            return None

        search_log: AiSearchAgentLog
        match (config.policy, log):
            case PolicyConfig.ExpectimaxPolicy(), ExpectimaxSearchLog():
                search_log = AiSearchAgentLog(
                    tree_size=log.tree_size,
                    tree_depth=config.policy.depth,
                )
            case PolicyConfig.MinimaxPolicy(), MinimaxSearchLog():
                search_log = AiSearchAgentLog(
                    tree_size=log.tree_size,
                    tree_depth=config.policy.depth,
                )
            case PolicyConfig.MctsPolicy(), MctsSearchLog():
                search_log = AiSearchAgentLog(
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
            AiSearchActionResult(
                action=action,
                result=result,
                search_log=search_log,
            )
        )

    @staticmethod
    def get_game_tree(
        gs: GameState,
        config: SearchPolicyConfig,
    ) -> AiSearchTreeResult | None:
        """
        Returns the expanded game tree given the state. This uses the
        AI config of the state. This does not perform the action.
        """

        state = AiSearchAgent.get_state(gs, config)
        action, log = AiSearchAgent._get_action(
            state,
            config,
            log_with_tree=True,
        )

        if action == None:
            return None

        if log.tree_root == None:
            raise RuntimeError("The policy didn't return tree!")

        return AiSearchTreeResult(
            best_action=action,
            game_tree=log.tree_root,
        )

    @staticmethod
    def _get_action(
        state: ISearchState[Action],
        config: SearchPolicyConfig,
        log_with_tree: bool = False,
    ) -> tuple[
        Action | None,
        (
            ExpectimaxSearchLog[Action]
            | MinimaxSearchLog[Action]
            | MctsSearchLog[Action]
        ),
    ]:
        """
        Helper method to dispatch to policy given the config to
        get its policy's best action and policy's log.
        """

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
                    exploration_const=config.policy.exploration_const,
                )
