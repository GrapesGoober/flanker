from dataclasses import dataclass
from typing import Literal

from flanker_ai.ai_agent import AiAgent
from flanker_ai.policies.expectimax_policy import ExpectimaxPolicy
from flanker_ai.unabstracted.random_heuristic_agent import RandomHeuristicAgent
from flanker_ai.waypoints.models import WaypointAction
from flanker_ai.waypoints.waypoints_converter import WaypointConverter
from flanker_core.gamestate import GameState
from flanker_core.models.components import InitiativeState
from flanker_core.models.vec2 import Vec2


@dataclass
class AiWaypointConfig:
    type: Literal["AiWaypointConfig"]
    waypoint_coordinates: list[Vec2]
    path_tolerance: float


@dataclass
class AiRandomHeuristicConfig:  # No config for this one
    type: Literal["AiRandomHeuristicConfig"]
    ...


@dataclass
class AiConfigComponent:
    faction: InitiativeState.Faction
    config: AiWaypointConfig | AiRandomHeuristicConfig


@dataclass
class _AiAgentInstanceComponent:
    faction: InitiativeState.Faction
    agent: AiAgent | RandomHeuristicAgent


class AiAgentFactory:

    @staticmethod
    def get_ai_config(
        gs: GameState,
        faction: InitiativeState.Faction,
    ) -> AiWaypointConfig | AiRandomHeuristicConfig:
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
    ) -> AiAgent | RandomHeuristicAgent:
        """Use the config to build an AI agent, or reuse agent if exists."""

        # Get the agent instance component.
        agent: AiAgent | RandomHeuristicAgent | None = None
        for _, agent_instance in gs.query(_AiAgentInstanceComponent):
            if agent_instance.faction != faction:
                continue
            agent = agent_instance.agent
            break
        # If not exist, create a new empty one
        if agent is None:
            config = AiAgentFactory.get_ai_config(gs, faction)
            match config:
                case AiWaypointConfig():
                    agent = AiAgent(
                        gs=gs,
                        faction=faction,
                        converter=WaypointConverter(
                            points=config.waypoint_coordinates,
                            path_tolerance=config.path_tolerance,
                        ),
                        policy=ExpectimaxPolicy[WaypointAction](depth=4),
                    )
                case AiRandomHeuristicConfig():
                    agent = RandomHeuristicAgent(
                        gs=gs,
                        faction=faction,
                    )

            gs.add_entity(_AiAgentInstanceComponent(faction=faction, agent=agent))

        return agent
