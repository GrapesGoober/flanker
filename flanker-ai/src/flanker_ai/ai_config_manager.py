from dataclasses import dataclass

from flanker_ai.unabstracted.random_heuristic_agent import RandomHeuristicAgent
from flanker_ai.waypoints.waypoints_minimax_agent import WaypointsMinimaxAgent
from flanker_core.gamestate import GameState
from flanker_core.models.components import InitiativeState
from flanker_core.models.vec2 import Vec2


@dataclass
class AiWaypointConfig:
    waypoint_coordinates: list[Vec2]
    path_tolerance: float


@dataclass
class AiRandomHeuristicConfig:  # No config for this one
    ...


@dataclass
class AiConfigComponent:
    faction: InitiativeState.Faction
    config: AiWaypointConfig | AiRandomHeuristicConfig


@dataclass
class _AiAgentInstance:
    faction: InitiativeState.Faction
    agent: WaypointsMinimaxAgent | RandomHeuristicAgent


class AiConfigManager:

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
    ) -> WaypointsMinimaxAgent | RandomHeuristicAgent:
        """Use the config to build an AI agent, or reuse agent if exists."""

        # Get the agent instance component.
        agent: WaypointsMinimaxAgent | RandomHeuristicAgent | None = None
        for _, agent_instance in gs.query(_AiAgentInstance):
            if agent_instance.faction != faction:
                continue
            agent = agent_instance.agent
            break
        # If not exist, create a new empty one
        if agent is None:
            config = AiConfigManager.get_ai_config(gs, faction)
            match config:
                case AiWaypointConfig():
                    # if len(config.waypoint_coordinates) == 0:
                    #     DEFAULT_GRID_SIZE = 20
                    #     config.path_tolerance = DEFAULT_GRID_SIZE
                    #     config.waypoint_coordinates = WaypointScheme.get_grid_coordinates(
                    #         gs, spacing=DEFAULT_GRID_SIZE, offset=DEFAULT_GRID_SIZE / 2
                    #     )
                    agent = WaypointsMinimaxAgent(
                        gs=gs,
                        faction=faction,
                        search_depth=4,
                        waypoint_coordinates=config.waypoint_coordinates,
                        path_tolerance=config.path_tolerance,
                    )
                case AiRandomHeuristicConfig():
                    agent = RandomHeuristicAgent(
                        gs=gs,
                        faction=faction,
                    )

            gs.add_entity(_AiAgentInstance(faction=faction, agent=agent))

        return agent
