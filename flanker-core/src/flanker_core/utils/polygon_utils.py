import math
from dataclasses import dataclass
from itertools import pairwise
from typing import Any, Callable

from flanker_core.models.vec2 import Vec2
from flanker_core.utils.intersect_utils import IntersectUtils


@dataclass
class Obstacle[T]:
    polyline: list[Vec2]
    metadata: T


@dataclass
class ObstacleIntersection[T]:
    obstacle: Obstacle[T]
    point: Vec2


class PolygonUtils:

    @staticmethod
    def is_inside(
        point: Vec2,
        polygon: list[Vec2],
    ) -> bool:
        """
        Checks whether a point is inside a polygon.
        Polygon must be closed loop that `polygon[-1] == polygon[0]`.
        """
        if len(polygon) <= 2:
            raise ValueError("`is_inside` need at least three vertices.")
        if polygon[-1] != polygon[0]:
            raise ValueError("Polygon is not closed loop.")

        # Create a line in arbitrary (right-ward) direction to count intersections
        # Direction doesn't matter. All results are the same.
        line_cast_to = Vec2(max(v.x for v in polygon) + 1, point.y)
        # Prevent this line from casting directly at a vertex
        line_cast_to = line_cast_to.rotated(1e-2) * 2  # Make the line longer
        # Cast and count
        intersect_points = IntersectUtils.get_intersects(
            line=(point, line_cast_to),
            polyline=polygon,
        )
        return len(intersect_points) % 2 != 0

    @staticmethod
    def get_reachable_polygon[T](
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

        vertices = PolygonUtils._get_relevant_vertices(obstacles)
        vertices = PolygonUtils._sort_verts_by_angle(
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
                    intersects = IntersectUtils.get_intersects(
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
                if PolygonUtils._is_colinear(polygon, new_point):
                    polygon[-1] = new_point
                    continue
                polygon.append(new_point)

        polygon.append(polygon[0])
        return polygon

    @staticmethod
    def clip_by_fov_cone(
        polyline: list[Vec2],
        center_point: Vec2,
        heading_degree: float,
        fov_degree: int = 90,
        radius: float = 1000,
    ) -> list[Vec2]:
        """Returns a new clipped a polygon to the specified cone."""

        # Create some rays that defines this FOV cone
        heading_rad = math.radians(heading_degree)
        forward_direction: Vec2 = Vec2(1, 0).rotated(heading_rad)
        forward_ray = forward_direction * radius
        half_angle_rad = math.radians(fov_degree / 2)
        left_ray: Vec2 = center_point + forward_ray.rotated(half_angle_rad)
        right_ray: Vec2 = center_point + forward_ray.rotated(-half_angle_rad)

        # Choose the two first intersection points of this FOV cone
        left_point = min(
            IntersectUtils.get_intersects(
                line=(center_point, left_ray), polyline=polyline
            ),
            key=lambda point: (center_point - point).length(),
        )
        right_point = min(
            IntersectUtils.get_intersects(
                line=(center_point, right_ray), polyline=polyline
            ),
            key=lambda point: (center_point - point).length(),
        )

        # Filter LOS polygon of any points outside of FOV
        threshold_rad: float = math.cos(half_angle_rad)
        new_los: list[Vec2] = []
        for vertex in polyline:
            direction = vertex - center_point

            if direction.length() < 1e-9:
                # Keep the center point
                new_los.append(vertex)
                continue

            # Using dot formula to filter the angle
            a: Vec2 = forward_direction
            b: Vec2 = direction.normalized()
            if a.dot(b) >= threshold_rad:
                new_los.append(vertex)

        # Add left points and right points back to the list
        # to represent the cut FOV edges.
        new_los.append(left_point)
        new_los.append(right_point)
        new_los.append(center_point - forward_direction * 1e-9)
        new_los = PolygonUtils._sort_verts_by_angle(center_point, new_los)
        new_los.append(new_los[0])  # Loop back to a closed polyline
        return new_los

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
                    intersects = IntersectUtils.get_intersects(
                        line=line,
                        polyline=other_obstacle.polyline,
                    )
                    vertices += intersects
        vertices = PolygonUtils._filter_colocated(vertices)
        return vertices

    @staticmethod
    def _filter_colocated(
        points: list[Vec2],
        tolerance: float = 1e-5,
    ) -> list[Vec2]:
        """Returns a new list that filtered redundant colocated points."""

        filtered_points: list[Vec2] = []
        for point in points:
            if not any(
                point.is_close(other, abs_tol=tolerance) for other in filtered_points
            ):
                filtered_points.append(point)
        return filtered_points

    # TODO make an angle method in Vec2? and reuse this sort inline?
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
