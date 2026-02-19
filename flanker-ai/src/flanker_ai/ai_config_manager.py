from dataclasses import dataclass

from flanker_ai.waypoints.waypoints_minimax_agent import WaypointsMinimaxAgent
from flanker_ai.waypoints.waypoints_scheme import WaypointScheme
from flanker_core.gamestate import GameState
from flanker_core.models.components import InitiativeState
from flanker_core.models.vec2 import Vec2


@dataclass
class AiConfigComponent:
    faction: InitiativeState.Faction
    waypoint_coordinates: list[Vec2]
    path_tolerance: float


@dataclass
class _AiAgentInstance:
    faction: InitiativeState.Faction
    agent: WaypointsMinimaxAgent


class AiConfigManager:

    @staticmethod
    def get_ai_config(
        gs: GameState,
        faction: InitiativeState.Faction,
    ) -> AiConfigComponent:
        # Get the config. If not exist, create a new empty one
        config: AiConfigComponent | None = None
        for _, c in gs.query(AiConfigComponent):
            if c.faction != faction:
                continue
            config = c
            break
        if config is None:
            gs.add_entity(
                config := AiConfigComponent(
                    faction=faction,
                    waypoint_coordinates=[],
                    path_tolerance=0,
                )
            )
        return config

    @staticmethod
    def get_agent(
        gs: GameState,
        faction: InitiativeState.Faction,
    ) -> WaypointsMinimaxAgent:
        """Use the `AiConfig` to build an AI agent."""

        # Get the agent instance component.
        agent: WaypointsMinimaxAgent | None = None
        for _, comp in gs.query(_AiAgentInstance):
            if comp.faction != faction:
                continue
            agent = comp.agent
            break
        # If not exist, create a new empty one
        if agent is None:
            config = AiConfigManager.get_ai_config(gs, faction)
            # Add a new set of waypoints if not exists.
            if len(config.waypoint_coordinates) == 0:
                DEFAULT_GRID_SIZE = 20
                config.path_tolerance = DEFAULT_GRID_SIZE
                config.waypoint_coordinates = WaypointScheme.get_grid_coordinates(
                    gs, spacing=DEFAULT_GRID_SIZE, offset=DEFAULT_GRID_SIZE / 2
                )
            agent = WaypointsMinimaxAgent(
                gs=gs,
                faction=faction,
                search_depth=4,
                waypoint_coordinates=config.waypoint_coordinates,
                path_tolerance=config.path_tolerance,
            )
            gs.add_entity(_AiAgentInstance(faction=faction, agent=agent))

        return agent
