from copy import deepcopy
from typing import Any

from flanker_ai.config_models import (
    PolicyConfig,
    SearchPolicyConfig,
    UnabstractedStateConfig,
    WaypointsStateConfig,
)
from flanker_ai.i_ai_agent import AiActionResult, IAiAgent
from flanker_ai.i_search_policy import ISearchPolicy
from flanker_ai.i_search_state import ISearchState
from flanker_ai.policies.expectimax_policy import ExpectimaxPolicy
from flanker_ai.policies.mcts_policy import MctsPolicy
from flanker_ai.policies.minimax_policy import MinimaxPolicy
from flanker_ai.policies.random_heuristic_policy import RandomHeuristicPolicy
from flanker_ai.policies.random_policy import RandomPolicy
from flanker_ai.policies.search_log_models import AiSearchLog
from flanker_ai.states.unabstracted.unabstracted_state import UnabstractedState
from flanker_ai.states.waypoints.waypoints_state import WaypointsState
from flanker_core.gamestate import GameState
from flanker_core.models.actions import Action
from flanker_core.models.components import InitiativeState
from flanker_core.models.outcomes import InvalidAction
from flanker_core.systems.action_system import ActionSystem


class AiSearchAgent(IAiAgent[AiSearchLog]):
    def __init__(
        self,
        faction: InitiativeState.Faction,
        rs: ISearchState[Action],
        policy: ISearchPolicy[Action, AiSearchLog],
    ) -> None:
        self.faction: InitiativeState.Faction = faction
        self.policy: ISearchPolicy[Action, AiSearchLog] = policy
        self.rs: ISearchState[Action] = rs

    def perform_action(self, gs: GameState) -> AiActionResult[AiSearchLog] | None:
        """
        Performs an action and return its result.
        Returns `None` if no legal actions possible.
        """

        # Prepare the representation and run the policy on it
        rs = deepcopy(self.rs)
        rs.update_state(gs)
        action, log = self.policy.get_action(rs)
        if action == None:
            return None

        result = ActionSystem.perform(gs, action)
        if isinstance(result, InvalidAction):
            return None

        # Prevent mutation shenanigans by returning a copy
        return deepcopy(
            AiActionResult(
                action=action,
                result=result,
                result_gs=gs,
                policy_log=log,
            )
        )

    @staticmethod
    def get_search_agent(
        gs: GameState,
        faction: InitiativeState.Faction,
        config: SearchPolicyConfig,
    ) -> "AiSearchAgent":
        """Use the config to build an AI agent, or reuse agent if exists."""

        policy_config = config.policy
        match policy_config:
            case PolicyConfig.ExpectimaxPolicy():
                policy = ExpectimaxPolicy[Action](
                    depth=policy_config.depth,
                )
            case PolicyConfig.MinimaxPolicy():
                policy = MinimaxPolicy[Action](
                    depth=policy_config.depth,
                )
            case PolicyConfig.MctsPolicy():
                match policy_config.simulation_policy:
                    case "random":
                        simulate_policy = RandomPolicy[Any]()
                    case "rh":
                        simulate_policy = RandomHeuristicPolicy()

                policy = MctsPolicy[Action](
                    max_iterations=policy_config.max_iterations,
                    max_simulate_length=policy_config.max_simulate_length,
                    simulate_policy=simulate_policy,
                )
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

        return AiSearchAgent(faction, state, policy)
