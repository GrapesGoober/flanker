from flanker_ai.unabstracted.models import ActionResult
from flanker_ai.waypoints.models import WaypointActions, WaypointsGraphGameState
from flanker_core.gamestate import GameState


class WaypointScheme:
    """Provides abstraction logic between waypoints-graph and game state"""

    @staticmethod
    def create_grid_waypoints(
        gs: GameState, spacing: float
    ) -> WaypointsGraphGameState: ...

    @staticmethod
    def deabstract_actions(
        actions: list[WaypointActions],
    ) -> list[ActionResult]: ...
