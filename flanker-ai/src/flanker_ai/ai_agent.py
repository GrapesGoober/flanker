from copy import deepcopy
from dataclasses import dataclass

from flanker_ai.components import (
    AiConfigComponent,
)
from flanker_ai.i_ai_policy import IAiPolicy
from flanker_ai.i_representation_state import IRepresentationState
from flanker_ai.actions import (
    Action,
    ActionResult,
    AssaultAction,
    AssaultActionResult,
    FireAction,
    FireActionResult,
    MoveAction,
    MoveActionResult,
)
from flanker_ai.policies.expectimax_policy import ExpectimaxPolicy
from flanker_ai.policies.random_heuristic_policy import RandomHeuristicPolicy
from flanker_ai.unabstracted.unabstracted_state import UnabstractedState
from flanker_ai.waypoints.models import WaypointAction
from flanker_ai.waypoints.waypoints_state import WaypointsState
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
    def __init__[TAction](
        self,
        gs: GameState,
        faction: InitiativeState.Faction,
        rs: IRepresentationState[TAction],
        policy: IAiPolicy[TAction],
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
            if ObjectiveSystem.get_winning_faction(self._gs) != None:
                break
            # Prepare the template into state usable for AI
            gs = self._rs.copy()
            gs.update_state(self._gs)
            # Check redundant moves (stop search)
            if halt_counter > _MAX_ACTION_PER_INITIATIVE:
                print(f"{self._faction.value} AI made useless actions, breaking")
                InitiativeSystem.flip_initiative(self._gs)
                break
            # Runs the abstracted graph search
            actions = self._policy.get_action_sequence(gs)
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
    def get_ai_config(
        gs: GameState,
        faction: InitiativeState.Faction,
    ) -> AiConfigComponent.AiConfigTypes:
        # Get the config. If not exist, create a new empty one
        for _, config_component in gs.query(AiConfigComponent):
            if config_component.faction != faction:
                continue
            return config_component.config
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
            config = AiAgent.get_ai_config(gs, faction)
            match config:
                case AiConfigComponent.WaypointsConfig():
                    agent = AiAgent(
                        gs=gs,
                        faction=faction,
                        rs=WaypointsState(
                            points=config.waypoint_coordinates,
                            path_tolerance=config.path_tolerance,
                        ),
                        policy=ExpectimaxPolicy[WaypointAction](depth=4),
                    )
                case AiConfigComponent.RandomHeuristicConfig():
                    agent = AiAgent(
                        gs=gs,
                        faction=faction,
                        rs=UnabstractedState(gs),
                        policy=RandomHeuristicPolicy(gs),
                    )
                case AiConfigComponent.UnabstractedConfig():
                    agent = AiAgent(
                        gs=gs,
                        faction=faction,
                        rs=UnabstractedState(gs),
                        policy=ExpectimaxPolicy[Action](depth=4),
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
                    return MoveActionResult(
                        action=action,
                        result_gs=self._gs,
                        reactive_fire_outcome=result.reactive_fire_outcome,
                    )
            case FireAction():
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
        return result
