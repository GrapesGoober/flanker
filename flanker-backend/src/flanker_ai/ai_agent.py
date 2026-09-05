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
from flanker_ai.i_policy import IPolicy
from flanker_ai.i_representation_state import IRepresentationState
from flanker_ai.policies.expectimax_policy import ExpectimaxPolicy, ExpectimaxSearchLog
from flanker_ai.policies.mcts_policy import MctsPolicy, MctsSearchLog
from flanker_ai.policies.minimax_policy import MinimaxPolicy, MinimaxSearchLog
from flanker_ai.policies.random_heuristic_policy import (
    RandomHeuristicLog,
    RandomHeuristicPolicy,
)
from flanker_ai.policies.random_policy import RandomPolicy, RandomSearchLog
from flanker_ai.states.unabstracted.unabstracted_state import UnabstractedState
from flanker_ai.states.waypoints.waypoints_state import WaypointsState
from flanker_core.gamestate import GameState
from flanker_core.models.actions import Action, ActionResult
from flanker_core.models.components import InitiativeState
from flanker_core.models.outcomes import InvalidAction
from flanker_core.systems.action_system import ActionSystem
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.objective_system import ObjectiveSystem


@dataclass
class AiActionResult:
    action: Action
    result: ActionResult
    result_gs: GameState
    search_size: int


@dataclass
class _AiAgentInstanceComponent:
    faction: InitiativeState.Faction
    agent: "AiAgent"


SearchLog = (
    MinimaxSearchLog
    | MctsSearchLog
    | ExpectimaxSearchLog
    | RandomHeuristicLog
    | RandomSearchLog
)


class AiAgent:
    def __init__(
        self,
        gs: GameState,
        faction: InitiativeState.Faction,
        rs: IRepresentationState[Action],
        policy: IPolicy[Action, SearchLog],
    ) -> None:
        self.gs = gs
        self.faction: InitiativeState.Faction = faction
        self.policy: IPolicy[Action, SearchLog] = policy
        self.rs: IRepresentationState[Action] = rs

    def play_initiative(
        self, max_action_per_initiative: int = 10
    ) -> list[AiActionResult]:
        """Have the agent play the entire initiative."""
        if InitiativeSystem.get_initiative(self.gs) != self.faction:
            return []

        halt_counter = 0
        action_results: list[AiActionResult] = []
        while InitiativeSystem.get_initiative(self.gs) == self.faction:
            # If win/lose condition is already met, pass
            if ObjectiveSystem.get_winning_faction(self.gs) != None:
                break

            # Check redundant moves (stop search)
            if halt_counter > max_action_per_initiative:
                InitiativeSystem.flip_initiative(self.gs)
                break

            # Prepare the representation and run the policy on it
            rs = deepcopy(self.rs)
            rs.update_state(self.gs)
            action, log = self.policy.get_action(rs)
            if action == None:
                InitiativeSystem.flip_initiative(self.gs)
                break

            result = ActionSystem.perform(self.gs, action)
            if isinstance(result, InvalidAction):
                InitiativeSystem.flip_initiative(self.gs)
                break

            search_size: int
            match log:
                case RandomHeuristicLog():
                    search_size = log.actions_length
                case MinimaxSearchLog():
                    search_size = log.tree_size
                case ExpectimaxSearchLog():
                    search_size = log.tree_size
                case MctsSearchLog():
                    search_size = log.tree_depth
                case RandomSearchLog():
                    search_size = log.actions_length

            ai_action_result = AiActionResult(
                action=action,
                result=result,
                result_gs=self.gs,
                search_size=search_size,
            )
            # Prevent mutation by creating a copy
            action_results.append(deepcopy(ai_action_result))
            halt_counter += 1
        return action_results

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
        policy: IPolicy[Action, SearchLog]
        state: IRepresentationState[Action]
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
