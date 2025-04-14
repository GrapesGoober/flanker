"""
Polygon System for 2D polygons & computing intersections.
"""

from dataclasses import dataclass
from typing import Iterator
from itertools import pairwise
from systems.ecs import Component, GameState
from systems.vec2 import Vec2


@dataclass
class Polygon(Component):
    """A 2D non-looping polygon component containing list of vertices (x, y)."""

    vertices: list[Vec2]
    flag: int = -1

    def on_add(self, gs: GameState) -> None:
        space = gs.system(PolygonSpace)
        if self not in space.polygons:
            space.polygons.append(self)

    def on_remove(self, gs: GameState) -> None:
        space = gs.system(PolygonSpace)
        if self in space.polygons:
            space.polygons.remove(self)


@dataclass
class Intersection:
    """Return type for `get_intersects`, containing the intersecting point and feature."""

    point: Vec2
    feature: Polygon


class PolygonSpace:
    """System pool for Polygons, for checking polygon intersections."""

    def __init__(self) -> None:
        self.polygons: list[Polygon] = []

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

    def get_intersects(
        self, start: Vec2, end: Vec2, mask: int = -1
    ) -> Iterator[Intersection]:
        """Returns iterator of intersection points between the line segment and features."""
        for feature in self.polygons:
            if feature.flag & mask:
                for b1, b2 in pairwise(feature.vertices):
                    if (
                        intsct := PolygonSpace._get_intersect(start, end, b1, b2)
                    ) is not None:
                        yield Intersection(intsct, feature)
