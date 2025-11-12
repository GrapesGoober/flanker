from itertools import pairwise
import math
from typing import Iterable

from core.components import CombatUnit, TerrainFeature, Transform
from core.gamestate import GameState
from core.systems.intersect_system import IntersectSystem
from core.utils.linear_transform import LinearTransform
from core.utils.vec2 import Vec2
from dataclasses import dataclass


@dataclass
class Intersection:
    """Represents intersection between line and terrain feature."""

    point: Vec2
    terrain: TerrainFeature
    terrain_id: int


class LosSystem:
    """Static system class for checking Line-of-Sight (LOS) for entities."""

    @staticmethod
    def check(gs: GameState, spotter_ent: int, target_pos: Vec2) -> bool:
        """Returns `True` if entity `source_id` can see entity `target_id`."""
        spotter_transform = gs.get_component(spotter_ent, Transform)
        spotter_unit = gs.get_component(spotter_ent, CombatUnit)

        intersects = IntersectSystem.get(
            gs=gs,
            start=spotter_transform.position,
            end=target_pos,
            mask=TerrainFeature.Flag.OPAQUE,
        )

        # Can see into one other terrain polygon
        passed_one_terrain = False
        spotter_terrain = spotter_unit.inside_terrains or []
        for intersect in intersects:
            # Doesn't count spotter's terrain
            if intersect.terrain_id in spotter_terrain:
                continue
            if not passed_one_terrain:
                passed_one_terrain = True
                continue
            # Can only see into one polygon
            if passed_one_terrain:
                return False
        return True

    @staticmethod
    def get_los_polygon(
        gs: GameState,
        spotter_pos: Vec2,
        radius: float = 1000,
    ) -> list[Vec2]:
        """Returns a polygon representing the LOS from a spotter position."""
        verts = LosSystem.get_sorted_verts(gs, spotter_pos)
        visible_points: list[Vec2] = []
        for vert in verts:
            center_ray = (vert - spotter_pos).normalized() * radius
            angle_jitter = 1e-6
            left_ray = center_ray.rotated(-angle_jitter)
            right_ray = center_ray.rotated(+angle_jitter)
            for ray in [left_ray, right_ray]:
                intersects = list(
                    LosSystem.get_intersect(
                        gs=gs,
                        start=spotter_pos,
                        end=spotter_pos + ray,
                        mask=TerrainFeature.Flag.OPAQUE,
                    )
                )
                if intersects:
                    intersects = LosSystem.sort_by_distance(intersects, spotter_pos)
                    # Use the second intersection point to allow see-into terrain
                    if len(intersects) > 1:
                        second_intersect = intersects[1]
                    else:
                        second_intersect = intersects[0]
                    LosSystem.add_point_if_noncolinear(
                        visible_points, second_intersect.point
                    )
                else:
                    LosSystem.add_point_if_noncolinear(
                        visible_points, spotter_pos + ray
                    )

        return visible_points

    @staticmethod
    def _is_inside(vertices: list[Vec2], point: Vec2) -> bool:
        """
        Checks whether a point is inside vertices.
        Assumes closed loop that `vertices[-1] == vertices[0]`.
        """
        line_cast_to = Vec2(max(v.x for v in vertices) + 1, point.y)
        intersect_points: list[Vec2] = []
        for b1, b2 in pairwise(vertices):
            if intersect := LosSystem._get_intersect(point, line_cast_to, b1, b2):
                # Due to tolerance, duplicate intersects needs to be filtered out
                if intersect not in intersect_points:
                    intersect_points.append(intersect)

        return len(intersect_points) % 2 != 0

    @staticmethod
    def get_sorted_verts(
        gs: GameState,
        spotter_pos: Vec2,
    ) -> list[Vec2]:
        """Get all terrain vertices sorted by angle."""
        all_verts: list[Vec2] = []
        for _, terrain, transform in gs.query(TerrainFeature, Transform):
            if (terrain.flag & TerrainFeature.Flag.OPAQUE) == 0:
                continue
            all_verts += LinearTransform.apply(terrain.vertices, transform)

        def angle_from_spotter(v: Vec2) -> float:
            # Vector from spotter_pos to vertex
            rel = v - spotter_pos
            # Compute angle relative to +x axis (0 radians)
            theta = math.atan2(rel.y, rel.x)
            # Normalize to [0, 2π)
            if theta < 0:
                theta += 2 * math.pi
            return theta

        return sorted(all_verts, key=angle_from_spotter)

    @staticmethod
    def add_point_if_noncolinear(visible_points: list[Vec2], new_point: Vec2) -> None:
        if len(visible_points) >= 2:
            a = visible_points[-2]
            b = visible_points[-1]
            c = new_point

            # If points are colinear, replace
            ab = b - a
            ac = c - a
            cross = ab.cross(ac)
            if abs(cross) < 1e-9:
                visible_points[-1] = new_point
                return

            # If points are colocated, don't append
            if visible_points[-1] == new_point:
                return

        visible_points.append(new_point)

    @staticmethod
    def sort_by_distance(
        verts: list[Intersection],
        spotter_pos: Vec2,
    ) -> list[Intersection]:
        """Sorts a list of intersection by distance from spotter."""

        def distance_from_spotter(v: Intersection) -> float:
            return (v.point - spotter_pos).length()

        return sorted(verts, key=distance_from_spotter)

    @staticmethod
    def get_intersect(
        gs: GameState,
        start: Vec2,
        end: Vec2,
        mask: int = -1,
    ) -> Iterable[Intersection]:
        """Yields intersections between the line segment and terrain."""
        for id, terrain, transform in gs.query(TerrainFeature, Transform):
            if terrain.flag & mask:
                vertices = LinearTransform.apply(terrain.vertices, transform)
                if terrain.is_closed_loop:
                    vertices.append(vertices[0])
                    # Ignore the terrain entity if the spotter is inside it,
                    # this allows spotter to see-out of a terrain
                    if LosSystem._is_inside(vertices, start):
                        # This rule doesn't apply to boundary terrain
                        if (terrain.flag & TerrainFeature.Flag.BOUNDARY) == 0:
                            continue
                for b1, b2 in pairwise(vertices):
                    point = LosSystem._get_intersect(start, end, b1, b2)
                    if point is not None:
                        yield Intersection(point, terrain, id)

    @staticmethod
    def _get_intersect(
        a1: Vec2,
        a2: Vec2,
        b1: Vec2,
        b2: Vec2,
        tol: float = 1e-9,
    ) -> Vec2 | None:
        """Return an (x, y) intersection point between 2 line segments."""
        da = a2 - a1  # Delta first segment a
        db = b2 - b1  # Delta second segment b
        if (denom := da.cross(db)) == 0:
            return None  # Lines are parallel
        diff = b1 - a1
        t = diff.cross(db) / denom  # t and a are parametric values for intersection,
        u = diff.cross(da) / denom  # along the length of the vectors using deltas
        if -tol <= t <= 1 + tol and -tol <= u <= 1 + tol:
            return a1 + da * t  # Offset p1 point by ua to get final point
        return None  # Intersection is outside the segments
