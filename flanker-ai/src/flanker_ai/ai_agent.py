from copy import deepcopy
from dataclasses import dataclass

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
from flanker_ai.components import AiConfigComponent, AiStallCountComponent
from flanker_ai.i_policy import IPolicy
from flanker_ai.i_representation_state import IRepresentationState
from flanker_ai.policies.expectimax_policy import ExpectimaxPolicy
from flanker_ai.policies.minimax_policy import MinimaxPolicy
from flanker_ai.policies.random_heuristic_policy import RandomHeuristicPolicy
from flanker_ai.states.unabstracted_state import UnabstractedState
from flanker_ai.states.waypoints_actions import WaypointAction
from flanker_ai.states.waypoints_state import WaypointsState
from flanker_core.gamestate import GameState
from flanker_core.models.components import InitiativeState
from flanker_core.models.outcomes import InvalidAction
from flanker_core.systems.assault_system import AssaultSystem
from flanker_core.systems.fire_system import FireSystem
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.move_system import MoveSystem
from flanker_core.systems.objective_system import ObjectiveSystem
from flanker_core.systems.pivot_system import PivotSystem

_MAX_ACTION_PER_INITIATIVE = 20
_MAX_STALL_LIMIT = 5


@dataclass
class _AiAgentInstanceComponent:
    faction: InitiativeState.Faction
    agent: "AiAgent"


class AiAgent:
    def __init__[TAction](
        self,
        gs: GameState,
        faction: InitiativeState.Faction,
        rs: IRepresentationState[TAction],
        policy: IPolicy[TAction],
    ) -> None:
        self._gs = gs
        self._faction: InitiativeState.Faction = faction
        self._policy = policy
        self._rs = rs
        self._rs.initialize_state(gs)

    def play_initiative(self) -> list[ActionResult]:
        """Have the agent play the entire initiative."""

        if InitiativeSystem.get_initiative(self._gs) != self._faction:
            return []

        halt_counter = 0
        action_results: list[ActionResult] = []
        while InitiativeSystem.get_initiative(self._gs) == self._faction:
            # If win/lose condition is already met, pass
            if ObjectiveSystem.get_winning_faction(self._gs) != None:
                break
            if result := self._gs.query(AiStallCountComponent):
                _, stall_comp = result[0]
            else:
                self._gs.add_entity(stall_comp := AiStallCountComponent())
            if stall_comp.stall_counter[self._faction] > _MAX_STALL_LIMIT:
                break

            # Check redundant moves (stop search)
            if halt_counter > _MAX_ACTION_PER_INITIATIVE:
                print(f"{self._faction.value} AI made useless actions, breaking")
                InitiativeSystem.flip_initiative(self._gs)
                break

            # Prepare the representation and run the policy on it
            _rs = self._rs.copy()
            _rs.update_state(self._gs)
            actions = self._policy.get_action_sequence(_rs)
            print(f"{self._faction.value} AI made action: {actions}")

            if actions == []:
                print(f"No valid action for {self._faction.value} AI, breaking")
                InitiativeSystem.flip_initiative(self._gs)
                break

            action = self._rs.deabstract_action(
                action=actions[0],
                gs=self._gs,
            )

            result = self._perform_action(action)
            if isinstance(result, InvalidAction):
                print(f"{self._faction.value} AI made invalid action, breaking")
                InitiativeSystem.flip_initiative(self._gs)
                break
            # These result objects would be used for logging
            # Thus, prevent mutation by creating a copy
            action_results.append(deepcopy(result))
            halt_counter += 1

        return action_results

    @staticmethod
    def get_state_config(
        gs: GameState,
        faction: InitiativeState.Faction,
    ) -> AiConfigComponent.StateConfigTypes:
        # Get the config. If not exist, create a new empty one
        for _, config_component in gs.query(AiConfigComponent):
            if config_component.faction != faction:
                continue
            return config_component.state_config
        raise ValueError(f"No AI config for {gs}")

    @staticmethod
    def get_policy_config(
        gs: GameState,
        faction: InitiativeState.Faction,
    ) -> AiConfigComponent.PolicyConfigTypes:
        # Get the config. If not exist, create a new empty one
        for _, config_component in gs.query(AiConfigComponent):
            if config_component.faction != faction:
                continue
            return config_component.policy_config
        raise ValueError(f"No AI config for {gs}")

    @staticmethod
    def get_agent(
        gs: GameState,
        faction: InitiativeState.Faction,
    ) -> "AiAgent":
        """Use the config to build an AI agent, or reuse agent if exists."""

        # Get the agent instance component.
        agent: AiAgent | None = None
        for _, agent_instance in gs.query(_AiAgentInstanceComponent):
            if agent_instance.faction != faction:
                continue
            agent = agent_instance.agent
            break
        # If not exist, create a new empty one
        if agent is None:
            state_config = AiAgent.get_state_config(gs, faction)
            policy_config = AiAgent.get_policy_config(gs, faction)

            match state_config:
                case AiConfigComponent.UnabstractedStateConfig():
                    rs = UnabstractedState(gs)
                    match policy_config:
                        case AiConfigComponent.ExpectimaxPolicyConfig():
                            policy = ExpectimaxPolicy[Action](depth=4)
                        case AiConfigComponent.MinimaxPolicyConfig():
                            policy = MinimaxPolicy[Action](depth=4)
                        case AiConfigComponent.RandomHeuristicPolicyConfig():
                            policy = RandomHeuristicPolicy[Action](gs)
                    agent = AiAgent(
                        gs=gs,
                        faction=faction,
                        rs=rs,
                        policy=policy,
                    )
                case AiConfigComponent.WaypointsStateConfig():
                    rs = WaypointsState(
                        points=state_config.waypoint_coordinates,
                        path_tolerance=state_config.path_tolerance,
                    )
                    match policy_config:
                        case AiConfigComponent.ExpectimaxPolicyConfig():
                            policy = ExpectimaxPolicy[WaypointAction](depth=4)
                        case AiConfigComponent.MinimaxPolicyConfig():
                            policy = MinimaxPolicy[WaypointAction](depth=4)
                        case AiConfigComponent.RandomHeuristicPolicyConfig():
                            policy = RandomHeuristicPolicy[WaypointAction](gs)
                    agent = AiAgent(
                        gs=gs,
                        faction=faction,
                        rs=rs,
                        policy=policy,
                    )

            gs.add_entity(_AiAgentInstanceComponent(faction=faction, agent=agent))

        return agent

    def _perform_action(
        self,
        action: Action,
    ) -> ActionResult | InvalidAction:
        match action:
            case MoveAction():
                result = MoveSystem.move(
                    self._gs,
                    action.unit_id,
                    action.to,
                )
                if not isinstance(result, InvalidAction):
                    stall_counter_ent = self._gs.query(AiStallCountComponent)
                    _, counter = stall_counter_ent[0]
                    if result.reactive_fire_outcome == None:
                        counter.stall_counter[self._faction] += 1
                    else:
                        counter.stall_counter[self._faction]
                    return MoveActionResult(
                        action=action,
                        result_gs=self._gs,
                        reactive_fire_outcome=result.reactive_fire_outcome,
                    )
            case FireAction():
                stall_counter_ent = self._gs.query(AiStallCountComponent)
                _, counter = stall_counter_ent[0]
                counter.stall_counter[self._faction] = 0
                result = FireSystem.fire(
                    self._gs,
                    action.unit_id,
                    action.target_id,
                )
                if not isinstance(result, InvalidAction):
                    return FireActionResult(
                        action=action,
                        result_gs=self._gs,
                        outcome=result.outcome,
                    )
            case AssaultAction():
                stall_counter_ent = self._gs.query(AiStallCountComponent)
                _, counter = stall_counter_ent[0]
                counter.stall_counter[self._faction] = 0
                result = AssaultSystem.assault(
                    self._gs,
                    action.unit_id,
                    action.target_id,
                )
                if not isinstance(result, InvalidAction):
                    return AssaultActionResult(
                        action=action,
                        result_gs=self._gs,
                        outcome=result.outcome,
                        reactive_fire_outcome=result.reactive_fire_outcome,
                    )
            case PivotAction():
                stall_counter_ent = self._gs.query(AiStallCountComponent)
                _, counter = stall_counter_ent[0]
                counter.stall_counter[self._faction] += 1
                result = PivotSystem.pivot(
                    self._gs,
                    action.unit_id,
                    action.degrees,
                )
                if not isinstance(result, InvalidAction):
                    return PivotActionResult(
                        action=action,
                        result_gs=self._gs,
                    )
        return result
