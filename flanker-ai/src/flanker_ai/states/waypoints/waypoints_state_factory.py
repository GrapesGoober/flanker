from flanker_ai.config_models import WaypointsStateConfig
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

        points: list[Vec2] = AiPointsExpansionService.get_points(
            gs=gs,
            config=config.waypoints,
        )

        return WaypointsState(
            points=points,
            path_tolerance=config.path_tolerance,
        )
