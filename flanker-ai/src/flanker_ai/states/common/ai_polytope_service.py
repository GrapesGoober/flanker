from flanker_core.gamestate import GameState
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.los_system import LosSystem


class AiPolytopeService:
    @staticmethod
    def get_los_polytope(
        gs: GameState,
    ) -> dict[Vec2, list[Vec2]]:
        los_polytope: dict[Vec2, list[Vec2]] = {}
        for x in range(10, 290, 10):
            for y in range(10, 290, 10):
                los_polytope[Vec2(x, y)] = LosSystem.get_los_polygon(
                    gs=gs,
                    spotter_pos=Vec2(x, y),
                )
        return los_polytope
