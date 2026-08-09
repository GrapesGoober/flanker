from flanker_core.gamestate import GameState
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.los_system import LosSystem
from flanker_core.utils.polygon_utils import PolygonUtils


class AiPolytopeService:
    @staticmethod
    def get_los_polytope(
        gs: GameState,
    ) -> dict[Vec2, list[Vec2]]:
        los_polytope: dict[Vec2, list[Vec2]] = {}
        for x in range(10, 290, 10):
            for y in range(10, 290, 10):
                polygon = LosSystem.get_los_polygon(
                    gs=gs,
                    spotter_pos=Vec2(x, y),
                )
                los_polytope[Vec2(x, y)] = polygon
        return los_polytope

    @staticmethod
    def get_los_polytope_fov_clipped(
        gs: GameState,
    ) -> dict[tuple[Vec2, float], list[Vec2]]:
        los_polytope: dict[tuple[Vec2, float], list[Vec2]] = {}
        for x in range(10, 290, 10):
            for y in range(10, 290, 10):
                for r in range(0, 360, 10):
                    polygon = LosSystem.get_los_polygon(
                        gs=gs,
                        spotter_pos=Vec2(x, y),
                    )
                    polygon = PolygonUtils.clip_by_fov_cone(
                        polyline=polygon,
                        center_point=Vec2(x, y),
                        heading_degree=r,
                    )
                    los_polytope[(Vec2(x, y), r)] = polygon
        return los_polytope
