from typing import Iterable, override

from flanker_core.gamestate import GameState
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.intersect_system import Intersection, IntersectSystem


class WaypointsIntersectSystem(IntersectSystem):
    @staticmethod
    @override
    def get(
        gs: GameState,
        start: Vec2,
        end: Vec2,
        mask: int = -1,
    ) -> Iterable[Intersection]:
        # This override is intended for move action validation.
        # All the possible (start, end) coordinate pairs are already
        # precomputed by the waypoints state initialization.

        # This doesn't need to be overriden since the AI demo
        # doesn't have un-walkable terrain
        ...
