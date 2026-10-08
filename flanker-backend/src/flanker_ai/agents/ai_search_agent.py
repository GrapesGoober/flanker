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
)
from flanker_ai.search_policies.mcts_policy import (
    MctsPolicy,
    MctsSearchLog,
)
from flanker_ai.search_policies.minimax_policy import (
    MinimaxPolicy,
    MinimaxSearchLog,
)
from flanker_ai.search_policies.random_heuristic_policy import (
    RandomHeuristicLog,
    RandomHeuristicPolicy,
)
from flanker_ai.search_policies.random_policy import (
    RandomPolicy,
    RandomSearchLog,
)
from flanker_ai.search_states.i_search_state import ISearchState
from flanker_ai.search_states.unabstracted.unabstracted_state import UnabstractedState
from flanker_ai.search_states.waypoints.waypoints_state import WaypointsState
from flanker_core.gamestate import GameState
from flanker_core.models.actions import Action, ActionResult
from flanker_core.models.outcomes import InvalidAction
from flanker_core.systems.action_system import ActionSystem

type AiSearchLog = (
    MinimaxSearchLog
    | MctsSearchLog
    | ExpectimaxSearchLog
    | RandomHeuristicLog
    | RandomSearchLog
)


class AiSearchAgent:

    @dataclass
    class ActionResult:
        action: Action
        result: ActionResult
        search_log: AiSearchLog

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
        log: AiSearchLog
        match config.policy:
            case PolicyConfig.ExpectimaxPolicy():
                action, log = ExpectimaxPolicy[Action].get_action(
                    rs=state, depth=config.policy.depth
                )
            case PolicyConfig.MinimaxPolicy():
                action, log = MinimaxPolicy[Action].get_action(
                    state=state, depth=config.policy.depth
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

                action, log = MctsPolicy[Action].get_action(
                    rs=state,
                    max_iterations=config.policy.max_iterations,
                    max_simulate_length=config.policy.max_simulate_length,
                    simulate_policy=simulate_policy,
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
                search_log=log,
            )
        )
