from dataclasses import dataclass
from itertools import pairwise
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


class NewIntersectSystem:
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
        vertices.append(vertices[0])
        max_x = max(vertices, key=lambda v: v.x).x
        start = ent_transform.position
        end = Vec2(max_x + 1, ent_transform.position.y)

        is_inside = False
        for b1, b2 in pairwise(vertices):
            point = IntersectSystem._get_intersect(start, end, b1, b2)
            if point is not None:
                is_inside = not is_inside
        return is_inside

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
                for b1, b2 in pairwise(vertices):
                    point = IntersectSystem._get_intersect(start, end, b1, b2)
                    if point is not None:
                        yield Intersection(point, terrain, id)

    @staticmethod
    def _get_intersect(a1: Vec2, a2: Vec2, b1: Vec2, b2: Vec2) -> Vec2 | None:
        """Return an (x, y) intersection point between 2 line segments."""
        da = a2 - a1  # Delta first segment a
        db = b2 - b1  # Delta second segment b
        if (denom := da.cross(db)) == 0:
            return None  # Lines are parallel
        diff = b1 - a1
        t = diff.cross(db) / denom  # t and a are parametric values for intersection,
        u = diff.cross(da) / denom  # along the length of the vectors using deltas
        if 0 <= t <= 1 and 0 <= u <= 1:
            return a1 + da * t  # Offset p1 point by ua to get final point
        return None  # Intersection is outside the segments
