from dataclasses import dataclass
from typing import Callable

from flanker_core.models.vec2 import Vec2
from flanker_core.utils.intersect_getter import IntersectGetter


@dataclass
class Obstacle[T]:
    polyline: list[Vec2]
    metadata: T


@dataclass
class Intersection[T]:
    obstacle: Obstacle[T]
    point: Vec2


class ReachabilityPolygon:
    @staticmethod
    def get_polygon[T](
        center_point: Vec2,
        obstacles: list[Obstacle[T]],
        criteria: Callable[[list[Intersection[T]]], Vec2],
        jitter_size: float = 1e-6,  # Smaller values will break t-u bezier checks
        radius: float = 1000,
    ) -> list[Vec2]:
        """
        Returns a polygon of all reachable region from the center point.
        """

        # TODO: consider inter-obstacle intersections too.
        verts: list[Vec2] = [
            vertex for obstacle in obstacles for vertex in obstacle.polyline
        ]
        los_polygon: list[Vec2] = []
        for vert in verts:
            direction = (vert - center_point).normalized()
            ray = direction * radius
            # Instead of casting one ray, casts two rays slightly to the left and right.
            # This prevents boundary sensitivity when casting rays at the vertices.
            jitter = direction.rotated(1.5708) * jitter_size
            left_point = center_point - jitter
            right_point = center_point + jitter
            for center_point in [left_point, right_point]:
                # Calculates intersections against each obstacle
                intersections: list[Intersection[T]] = []
                for obstacle in obstacles:
                    intersects = IntersectGetter.get_intersects(
                        line=(center_point, center_point + ray),
                        polyline=obstacle.polyline,
                    )
                    for intersect in intersects:
                        intersections.append(
                            Intersection(
                                obstacle=obstacle,
                                point=intersect,
                            )
                        )
                intersections = sorted(
                    intersections,
                    key=lambda i: (i.point - center_point).length(),
                )

                # Choose which point from the intersects to append
                if intersections != []:
                    new_point: Vec2 = criteria(intersections)
                else:  # No intersects, use fallback point using the ray
                    new_point = center_point + ray

                # If the new point is close enough to the target vertex,
                # assume that the point is aimed there and lands close enough
                if (new_point - vert).length() < 1e-3:
                    new_point = vert
                # If points are colocated, don't append
                if los_polygon and los_polygon[-1] == new_point:
                    continue
                # If points are colinear, replace instead of append
                if ReachabilityPolygon._is_colinear(los_polygon, new_point):
                    los_polygon[-1] = new_point
                    continue
                los_polygon.append(new_point)

        los_polygon.append(los_polygon[0])
        return los_polygon

    @staticmethod
    def _is_colinear(
        previous_points: list[Vec2],
        new_point: Vec2,
    ) -> bool:
        """
        Returns whether points are colinear from the previous other points.
        """
        if len(previous_points) >= 2:
            a = previous_points[-2]
            b = previous_points[-1]
            c = new_point
            ab = b - a
            ac = c - a
            cross = ab.cross(ac)
            if abs(cross) < 1e-9:
                return True

        return False
