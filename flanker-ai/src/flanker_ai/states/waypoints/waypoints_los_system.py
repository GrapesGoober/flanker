from typing import override

from flanker_core.gamestate import GameState
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.los_system import LosSystem


class WaypointsLosSystem(LosSystem):
    @staticmethod
    @override
    def has_los(gs: GameState, spotter_pos: Vec2, target_pos: Vec2) -> bool:
        raise NotImplementedError()
