from dataclasses import dataclass

from flanker_ai.waypoints.waypoints_minimax_player import WaypointsMinimaxPlayer
from flanker_ai.waypoints.waypoints_scheme import WaypointScheme
from flanker_core.gamestate import GameState
from flanker_core.models.components import InitiativeState
from flanker_core.models.vec2 import Vec2


@dataclass
class AiConfigComponent:
    faction: InitiativeState.Faction
    waypoint_coordinates: list[Vec2]


@dataclass
class _AiPlayerInstance:
    faction: InitiativeState.Faction
    player: WaypointsMinimaxPlayer


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
                )
            )
        return config

    @staticmethod
    def get_player(
        gs: GameState,
        faction: InitiativeState.Faction,
    ) -> WaypointsMinimaxPlayer:
        """Use the `AiConfig` to build an AI player."""

        # Get the player instance component.
        player: WaypointsMinimaxPlayer | None = None
        for _, comp in gs.query(_AiPlayerInstance):
            if comp.faction != faction:
                continue
            player = comp.player
            break
        # If not exist, create a new empty one
        if player is None:
            config = AiConfigManager.get_ai_config(gs, faction)
            # Add a new set of waypoints if not exists.
            if len(config.waypoint_coordinates) == 0:
                config.waypoint_coordinates = WaypointScheme.get_grid_coordinates(
                    gs, spacing=20, offset=10
                )
            player = WaypointsMinimaxPlayer(
                gs=gs,
                faction=faction,
                search_depth=4,
                waypoint_coordinates=config.waypoint_coordinates,
                path_tolerance=10,
            )
            gs.add_entity(_AiPlayerInstance(faction=faction, player=player))

        return player
