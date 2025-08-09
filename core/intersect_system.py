from dataclasses import dataclass
from itertools import pairwise
from typing import Iterable
from core.components import TerrainFeature, Transform
from core.gamestate import GameState
from core.utils.vec2 import Vec2
from core.utils.linear_transform import LinearTransform


@dataclass
class Intersection:
    """Represents intersection between line and terrain feature."""

    point: Vec2
    terrain: TerrainFeature
    terrain_id: int


class IntersectSystem:
    """ECS system for finding line and terrain feature intersections."""

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
                    if (intsct := IntersectSystem._get(start, end, b1, b2)) is not None:
                        yield Intersection(intsct, terrain, id)

    @staticmethod
    def _get(a1: Vec2, a2: Vec2, b1: Vec2, b2: Vec2) -> Vec2 | None:
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
