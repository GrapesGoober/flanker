from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from flanker_ai.components import AiConfigComponent
from flanker_ai.config_models import (
    HeuristicPolicyConfig,
    PointsConfig,
    PolicyConfig,
    SearchPolicyConfig,
    UnabstractedStateConfig,
    WaypointsStateConfig,
)
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
from flanker_core.models.actions import Action, ActionResult
from flanker_core.models.components import InitiativeState
from flanker_core.models.outcomes import InvalidAction
from flanker_core.systems.action_system import ActionSystem


@dataclass
class AiActionResult:
    action: Action
    result: ActionResult
    result_gs: GameState
    search_log: AiSearchLog


@dataclass
class _AiAgentInstanceComponent:
    faction: InitiativeState.Faction
    agent: "AiAgent"


class AiAgent:
    def __init__(
        self,
        gs: GameState,
        faction: InitiativeState.Faction,
        rs: ISearchState[Action],
        policy: ISearchPolicy[Action, AiSearchLog],
    ) -> None:
        self.gs = gs
        self.faction: InitiativeState.Faction = faction
        self.policy: ISearchPolicy[Action, AiSearchLog] = policy
        self.rs: ISearchState[Action] = rs

    def perform_action(self, gs: GameState) -> AiActionResult | None:
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

        result = ActionSystem.perform(self.gs, action)
        if isinstance(result, InvalidAction):
            return None

        # Prevent mutation shenanigans by returning a copy
        return deepcopy(
            AiActionResult(
                action=action,
                result=result,
                result_gs=self.gs,
                search_log=log,
            )
        )

    @staticmethod
    def get_agent(
        gs: GameState,
        faction: InitiativeState.Faction,
    ) -> "AiAgent":
        """Use the config to build an AI agent, or reuse agent if exists."""

        # Get the agent instance component if already exists
        for _, agent_instance in gs.query(_AiAgentInstanceComponent):
            if agent_instance.faction != faction:
                continue
            return agent_instance.agent

        # If not exist, create a new empty one using config
        config_component: AiConfigComponent | None = None
        for _, component in gs.query(AiConfigComponent):
            if component.faction == faction:
                config_component = component
                break
        if config_component == None:
            raise ValueError("AiConfigComponent not found")

        # Config found, create the agent
        policy: ISearchPolicy[Action, AiSearchLog]
        state: ISearchState[Action]
        match config_component.config:
            case HeuristicPolicyConfig():
                # TODO: need a better framework for rule-based policies.
                # It should not take the same states as search based, since
                # its use case is different.
                policy = RandomHeuristicPolicy()
                state = UnabstractedState(
                    move_pool_config=PointsConfig.Random(
                        type="Random",
                        count=10,
                    ),
                    move_filter_config=[],
                )
            case SearchPolicyConfig():
                policy_config = config_component.config.policy
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
                match config_component.config.state:
                    case UnabstractedStateConfig():
                        # The unabstracted state uses lazy move candidate filtering
                        state_config = config_component.config.state
                        state = UnabstractedState(
                            move_pool_config=state_config.move_candidates_pool,
                            move_filter_config=state_config.move_candidates_filter,
                        )
                    case WaypointsStateConfig():
                        state_config = config_component.config.state
                        state = WaypointsState(
                            waypoints_config=state_config.waypoints,
                            move_filter_config=state_config.move_candidates_filter,
                            path_tolerance=state_config.path_tolerance,
                        )

        agent = AiAgent(gs, faction, state, policy)
        gs.add_entity(
            _AiAgentInstanceComponent(
                faction=faction,
                agent=agent,
            )
        )
        return agent
