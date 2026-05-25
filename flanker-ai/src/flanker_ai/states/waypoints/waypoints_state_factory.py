from flanker_ai.config_models import WaypointsStateConfig
from flanker_ai.states.waypoints.waypoints_generator_service import (
    WaypointsGeneratorService,
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

        points: list[Vec2]
        match config.points:
            case WaypointsStateConfig.HandDrawnConfig():
                points = config.points.waypoint_coordinates
            case WaypointsStateConfig.GridConfig():
                points = WaypointsGeneratorService.get_grid_coordinates(
                    gs=gs,
                    spacing=config.points.spacing,
                    offset=config.points.offset,
                )
            case WaypointsStateConfig.VoronoiConfig():
                raise NotImplementedError()

        if config.expansion != None:
            match config.expansion.type:
                case "LineBased":
                    points = WaypointsGeneratorService.expand_waypoints_interrupt(
                        gs=gs,
                        initial_waypoints=points,
                        iterations=config.expansion.iterations,
                        prune_frequency=config.expansion.prune_frequency,
                    )
                case "Polygonal":
                    raise NotImplementedError()

        return WaypointsState(
            points=points,
            path_tolerance=config.path_tolerance,
        )
