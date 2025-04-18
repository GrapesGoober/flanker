from dataclasses import dataclass
from itertools import pairwise
from typing import Iterable
from components import Transform, TerrainFeature
from vec2 import Vec2
import esper


@dataclass
class Intersection:
    """Return type for `get_intersects`, containing the intersecting point and feature."""

    point: Vec2
    feature: TerrainFeature


class Intersects:
    @staticmethod
    def get(start: Vec2, end: Vec2, mask: int = -1) -> Iterable[Intersection]:
        """Returns iterable of intersection points between the line segment and features."""
        for _, (pos, feature) in esper.get_components(Transform, TerrainFeature):
            adjusted_vertices = [v + pos.position for v in feature.vertices]
            if feature.flag & mask:
                for b1, b2 in pairwise(adjusted_vertices):
                    if (intsct := Intersects._get(start, end, b1, b2)) is not None:
                        yield Intersection(intsct, feature)

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
