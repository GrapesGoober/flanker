from copy import deepcopy

from flanker_ai.ai_action_result import AiActionResult
from flanker_ai.config_models import (
    PolicyConfig,
    SearchPolicyConfig,
    UnabstractedStateConfig,
    WaypointsStateConfig,
)
from flanker_ai.search_policies.expectimax_policy import ExpectimaxPolicy
from flanker_ai.search_policies.mcts_policy import MctsPolicy
from flanker_ai.search_policies.minimax_policy import MinimaxPolicy
from flanker_ai.search_policies.random_heuristic_policy import RandomHeuristicPolicy
from flanker_ai.search_policies.random_policy import RandomPolicy
from flanker_ai.search_policies.search_log_models import AiSearchLog
from flanker_ai.search_states.i_search_state import ISearchState
from flanker_ai.search_states.unabstracted.unabstracted_state import UnabstractedState
from flanker_ai.search_states.waypoints.waypoints_state import WaypointsState
from flanker_core.gamestate import GameState
from flanker_core.models.actions import Action
from flanker_core.models.outcomes import InvalidAction
from flanker_core.systems.action_system import ActionSystem
from flanker_core.systems.initiative_system import InitiativeSystem


class AiSearchAgent:

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
    ) -> AiActionResult[AiSearchLog] | None:
        """
        Performs an action and return its result.
        Returns `None` if no legal actions possible.
        """

        match config.policy:
            case PolicyConfig.ExpectimaxPolicy():
                policy = ExpectimaxPolicy[Action](
                    depth=config.policy.depth,
                )
            case PolicyConfig.MinimaxPolicy():
                policy = MinimaxPolicy[Action](
                    depth=config.policy.depth,
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

                policy = MctsPolicy[Action](
                    max_iterations=config.policy.max_iterations,
                    max_simulate_length=config.policy.max_simulate_length,
                    simulate_policy=simulate_policy,
                )

        # Prepare the representation and run the policy on it
        state = AiSearchAgent.get_state(gs, config)
        action, log = policy.get_action(state)
        if action == None:
            return None

        result = ActionSystem.perform(gs, action)
        if isinstance(result, InvalidAction):
            return None

        # Prevent mutation shenanigans by returning a copy
        return deepcopy(
            AiActionResult(
                faction=InitiativeSystem.get_initiative(gs),
                action=action,
                result=result,
                policy_log=log,
            )
        )
