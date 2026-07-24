import math
from dataclasses import dataclass
from itertools import pairwise
from typing import Any, Callable

from flanker_core.models.vec2 import Vec2
from flanker_core.utils.intersect_getter import IntersectGetter


@dataclass
class Obstacle[T]:
    polyline: list[Vec2]
    metadata: T


@dataclass
class ObstacleIntersection[T]:
    obstacle: Obstacle[T]
    point: Vec2


class ReachabilityPolygon:
    @staticmethod
    def get_polygon[T](
        center_point: Vec2,
        obstacles: list[Obstacle[T]],
        criteria: Callable[[list[ObstacleIntersection[T]]], Vec2],
        jitter_size: float = 1e-6,  # Smaller values will break t-u bezier checks
        # TODO: consider an explicit boundary box instead?
        radius: float = 1000,
    ) -> list[Vec2]:
        """
        Returns a polygon of all reachable region from the center point.
        """

        vertices = ReachabilityPolygon._get_relevant_vertices(obstacles)
        vertices = ReachabilityPolygon._sort_verts_by_angle(
            center_point=center_point,
            verts=vertices,
        )
        polygon: list[Vec2] = []
        for target_vertex in vertices:
            direction = (target_vertex - center_point).normalized()
            ray = direction * radius
            # Instead of casting one ray, casts two rays slightly to the left and right.
            # This prevents boundary sensitivity when casting rays at the vertices.
            jitter = direction.rotated(1.5708) * jitter_size
            left_point = center_point - jitter
            right_point = center_point + jitter
            for cast_from in [left_point, right_point]:
                # Calculates intersections against each obstacle
                intersections: list[ObstacleIntersection[T]] = []
                for obstacle in obstacles:
                    intersects = IntersectGetter.get_intersects(
                        line=(cast_from, cast_from + ray),
                        polyline=obstacle.polyline,
                    )
                    for intersect in intersects:
                        intersections.append(
                            ObstacleIntersection(
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

                # Snap new point to target vertex
                if new_point.is_close(target_vertex, abs_tol=1e-3):
                    new_point = target_vertex
                # If points are colocated, don't append
                if polygon and polygon[-1].is_close(new_point):
                    continue
                # If points are colinear, replace instead of append
                if ReachabilityPolygon._is_colinear(polygon, new_point):
                    polygon[-1] = new_point
                    continue
                polygon.append(new_point)

        polygon.append(polygon[0])
        return polygon

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

    @staticmethod
    def _get_relevant_vertices(
        obstacles: list[Obstacle[Any]],
    ) -> list[Vec2]:
        """
        Returns relevant vertices to cast against for polygon.
        """
        vertices: list[Vec2] = []
        for obstacle in obstacles:
            # FIXME: since polyline is closed loop, its [0] == [-1]
            vertices += obstacle.polyline

        for obstacle in obstacles:
            for other_obstacle in obstacles:
                for line in pairwise(obstacle.polyline):
                    intersects = IntersectGetter.get_intersects(
                        line=line,
                        polyline=other_obstacle.polyline,
                    )
                    vertices += intersects
        vertices = ReachabilityPolygon._filter_colocated(vertices)
        return vertices

    @staticmethod
    def _sort_verts_by_angle(
        center_point: Vec2,
        verts: list[Vec2],
    ) -> list[Vec2]:
        """Sort vertices by the angle from a point."""

        def angle_from_center(v: Vec2) -> float:
            rel = v - center_point
            theta = math.atan2(rel.y, rel.x)
            if theta < 0:
                theta += 2 * math.pi
            return theta

        return sorted(verts, key=angle_from_center)

    @staticmethod
    def _filter_colocated(
        points: list[Vec2],
        tolerance: float = 1e-5,
    ) -> list[Vec2]:
        """Filter"""

        filtered_points: list[Vec2] = []
        for point in points:
            if not any(
                point.is_close(other, abs_tol=tolerance) for other in filtered_points
            ):
                filtered_points.append(point)
        return filtered_points
