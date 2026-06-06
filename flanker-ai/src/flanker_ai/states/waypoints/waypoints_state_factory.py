from flanker_ai.config_models import PointsConfig, WaypointsStateConfig
from flanker_ai.states.common.ai_points_expansion_service import (
    AiPointsExpansionService,
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
        initial_points_config = config.waypoints.initial_points
        match initial_points_config:
            case PointsConfig.HandDrawnConfig():
                points = initial_points_config.points
            case PointsConfig.GridConfig():
                points = AiPointsExpansionService.get_grid_coordinates(
                    gs=gs,
                    spacing=initial_points_config.spacing,
                    offset=initial_points_config.offset,
                )
            case PointsConfig.VoronoiConfig():
                raise NotImplementedError()

        expansion_config = config.waypoints.expansion
        if expansion_config != None:
            match expansion_config.type:
                case "LineBased":
                    points = AiPointsExpansionService.expand_waypoints_interrupt(
                        gs=gs,
                        initial_waypoints=points,
                        iterations=expansion_config.iterations,
                        prune_iterations=expansion_config.prune_iterations,
                    )
                case "Polygonal":
                    raise NotImplementedError()

        return WaypointsState(
            points=points,
            path_tolerance=config.path_tolerance,
        )
