from dataclasses import dataclass
from typing import Iterable

from core.components import TerrainFeature, Transform
from core.gamestate import GameState
from core.utils.vec2 import Vec2
from core.utils.linear_transform import LinearTransform
from shapely import (
    MultiPoint,
    Point,
    Polygon,
    LineString,
)


@dataclass
class Intersection:
    """Represents intersection between line and terrain feature."""

    point: Vec2
    terrain: TerrainFeature
    terrain_id: int


class IntersectSystem:
    """ECS system for finding line and terrain feature intersections."""

    @staticmethod
    def is_inside(gs: GameState, terrain_id: int, ent: int) -> bool:
        """Checks whether the entity is inside the closed terrain feature."""
        ent_transform = gs.get_component(ent, Transform)
        terrain = gs.get_component(terrain_id, TerrainFeature)
        terrain_transform = gs.get_component(terrain_id, Transform)
        if not terrain.is_closed_loop:
            return False

        # Cast a line from the ent to the right
        # The end point must be further (outside) of polygon
        vertices = LinearTransform.apply(terrain.vertices, terrain_transform)
        geom = Polygon([(v.x, v.y) for v in vertices])
        point = Point((ent_transform.position.x, ent_transform.position.y))

        return point.within(geom)

    @staticmethod
    def get(
        gs: GameState, start: Vec2, end: Vec2, mask: int = -1
    ) -> Iterable[Intersection]:
        """Yields intersections between the line segment and terrain."""
        for id, terrain, transform in gs.query(TerrainFeature, Transform):
            if terrain.flag & mask:
                vertices = LinearTransform.apply(terrain.vertices, transform)
                if terrain.is_closed_loop:
                    vertices.append(vertices[0])
                poly = LineString([(v.x, v.y) for v in vertices])
                line = LineString([(start.x, start.y), (end.x, end.y)])
                intersection = line.intersection(poly)
                points: list[Vec2] = []

                if intersection.is_empty:
                    continue

                if isinstance(intersection, Point):
                    points.append(Vec2(intersection.x, intersection.y))
                elif isinstance(intersection, MultiPoint):
                    points += [Vec2(pt.x, pt.y) for pt in intersection.geoms]

                for p in points:
                    if p == start or p == end:
                        continue
                    yield Intersection(p, terrain, id)
