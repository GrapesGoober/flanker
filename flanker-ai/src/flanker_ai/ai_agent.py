from copy import deepcopy
from dataclasses import dataclass
from typing import Callable

from flanker_ai.actions import (
    Action,
    ActionResult,
    AssaultAction,
    AssaultActionResult,
    FireAction,
    FireActionResult,
    MoveAction,
    MoveActionResult,
    PivotAction,
    PivotActionResult,
)
from flanker_ai.components import AiConfigComponent
from flanker_ai.config_models import (
    HeuristicPolicyConfig,
    PointsConfig,
    SearchPolicyConfig,
    UnabstractedStateConfig,
    WaypointsStateConfig,
)
from flanker_ai.i_policy import IPolicy
from flanker_ai.i_representation_state import IRepresentationState
from flanker_ai.policies.expectimax_policy import ExpectimaxPolicy
from flanker_ai.policies.minimax_policy import MinimaxPolicy
from flanker_ai.policies.random_heuristic_policy import RandomHeuristicPolicy
from flanker_ai.states.common.ai_points_expansion_service import (
    AiPointsExpansionService,
)
from flanker_ai.states.unabstracted.unabstracted_state import UnabstractedState
from flanker_ai.states.waypoints.waypoints_state import WaypointsState
from flanker_core.gamestate import GameState
from flanker_core.models.components import InitiativeState
from flanker_core.models.outcomes import InvalidAction
from flanker_core.systems.assault_system import AssaultSystem
from flanker_core.systems.fire_system import FireSystem
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.move_system import MoveSystem
from flanker_core.systems.objective_system import ObjectiveSystem

_MAX_ACTION_PER_INITIATIVE = 20


@dataclass
class _AiAgentInstanceComponent:
    faction: InitiativeState.Faction
    agent: "AiAgent"


class AiAgent:
    def __init__(
        self,
        gs: GameState,
        faction: InitiativeState.Faction,
        rs: IRepresentationState[Action],
        policy: IPolicy[Action],
    ) -> None:
        self.gs = gs
        self.faction: InitiativeState.Faction = faction
        self.policy: IPolicy[Action] = policy
        self.rs: IRepresentationState[Action] = rs

    def play_initiative(
        self,
        callback: Callable[[], None] | None = None,
    ) -> list[ActionResult]:
        """Have the agent play the entire initiative."""

        initiative_system = self.gs.get(InitiativeSystem)
        if initiative_system.get_initiative(self.gs) != self.faction:
            return []

        halt_counter = 0
        action_results: list[ActionResult] = []
        while initiative_system.get_initiative(self.gs) == self.faction:
            # If win/lose condition is already met, pass
            objective_system = self.gs.get(ObjectiveSystem)
            if objective_system.get_winning_faction(self.gs) != None:
                break

            # Check redundant moves (stop search)
            if halt_counter > _MAX_ACTION_PER_INITIATIVE:
                initiative_system.flip_initiative(self.gs)
                break

            # Prepare the representation and run the policy on it
            rs = deepcopy(self.rs)
            rs.update_state(self.gs)
            actions = self.policy.get_action_sequence(rs, callback)

            if actions == []:
                initiative_system.flip_initiative(self.gs)
                break

            action = actions[0]

            result = self._perform_action(action)
            if isinstance(result, InvalidAction):
                initiative_system.flip_initiative(self.gs)
                break
            # These result objects would be used for logging
            # Thus, prevent mutation by creating a copy
            action_results.append(deepcopy(result))
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
        policy: IPolicy[Action]
        state: IRepresentationState[Action]
        match config_component.config:
            case HeuristicPolicyConfig():
                # TODO: need a better framework for rule-based policies.
                # It should not take the same states as search based, since
                # its use case is different.
                policy = RandomHeuristicPolicy(gs)
                state = UnabstractedState(
                    gs=gs,
                    move_candidates_config=PointsConfig(
                        initial_points=PointsConfig.RandomConfig(
                            type="Random",
                            count=10,
                        ),
                        use_combat_unit_positions=False,
                        expansions=[],
                    ),
                    divide_moves_per_unit=False,
                )
            case SearchPolicyConfig():
                match config_component.config.policy_type:
                    case "Expectimax":
                        policy = ExpectimaxPolicy[Action](depth=4)
                    case "Minimax":
                        policy = MinimaxPolicy[Action](depth=4)
                match config_component.config.state:
                    case UnabstractedStateConfig():
                        # The unabstracted state uses lazy waypoint expansion
                        state_config = config_component.config.state
                        state = UnabstractedState(
                            gs,
                            move_candidates_config=state_config.move_candidates,
                            divide_moves_per_unit=state_config.divide_moves_per_unit,
                        )
                    case WaypointsStateConfig():
                        state_config = config_component.config.state
                        # TODO Waypoints state doesn't yet have lazy
                        # waypoint expansion, so it just takes waypoints
                        waypoints = AiPointsExpansionService.get_points(
                            gs=gs,
                            config=state_config.waypoints,
                        )
                        state = WaypointsState(
                            points=waypoints,
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

    def _perform_action(
        self,
        action: Action,
    ) -> ActionResult | InvalidAction:
        assault_system = self.gs.get(AssaultSystem)
        fire_system = self.gs.get(FireSystem)
        move_system = self.gs.get(MoveSystem)
        match action:
            case MoveAction():
                result = move_system.move(
                    self.gs,
                    action.unit_id,
                    action.to,
                )
                if not isinstance(result, InvalidAction):
                    return MoveActionResult(
                        action=action,
                        result_gs=self.gs,
                        reactive_fire_outcome=result.reactive_fire_outcome,
                    )
            case PivotAction():
                result = move_system.pivot(
                    self.gs,
                    action.unit_id,
                    action.to,
                )
                if not isinstance(result, InvalidAction):
                    return PivotActionResult(
                        action=action,
                        result_gs=self.gs,
                        reactive_fire_outcome=result.reactive_fire_outcome,
                    )
            case FireAction():
                result = fire_system.fire(
                    self.gs,
                    action.unit_id,
                    action.target_id,
                )
                if not isinstance(result, InvalidAction):
                    return FireActionResult(
                        action=action,
                        result_gs=self.gs,
                        outcome=result.outcome,
                    )
            case AssaultAction():
                result = assault_system.assault(
                    self.gs,
                    action.unit_id,
                    action.target_id,
                )
                if not isinstance(result, InvalidAction):
                    return AssaultActionResult(
                        action=action,
                        result_gs=self.gs,
                        outcome=result.outcome,
                        reactive_fire_outcome=result.reactive_fire_outcome,
                    )
            case _:
                raise Exception(f"Unknown action {action}")
        return result
