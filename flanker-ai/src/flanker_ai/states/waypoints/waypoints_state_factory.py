from flanker_ai.config_models import WaypointsStateConfig
from flanker_ai.states.waypoints.waypoints_placement_service import (
    WaypointsPlacementService,
)
from flanker_ai.states.waypoints.waypoints_state import WaypointsState
from flanker_core.gamestate import GameState
from flanker_core.models.vec2 import Vec2


class WaypointsStateFactory:
    """
    Factory class for creating waypoints state from config.
    """

    @staticmethod
    def create_state(
        gs: GameState,
        config: WaypointsStateConfig,
    ) -> WaypointsState:
        """
        Create a new waypoints state from game state and a config.
        """

        points_config = config.points
        points: list[Vec2]
        match points_config:
            case WaypointsStateConfig.HandDrawnConfig():
                points = points_config.waypoint_coordinates
            case WaypointsStateConfig.GridConfig():
                points = WaypointsPlacementService.get_grid_coordinates(
                    gs=gs,
                    spacing=points_config.spacing,
                    offset=points_config.offset,
                )
            case WaypointsStateConfig.VoronoiConfig():
                raise NotImplementedError()

        return WaypointsState(
            points=points,
            path_tolerance=config.path_tolerance,
        )
