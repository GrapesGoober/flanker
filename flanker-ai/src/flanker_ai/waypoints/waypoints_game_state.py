from flanker_ai.i_game_state import IGameState
from flanker_ai.waypoints.models import WaypointAction


class WaypointsGameState(IGameState[WaypointAction]):

    def __init__(self) -> None:
        super().__init__()
