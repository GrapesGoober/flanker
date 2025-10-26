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
        range: float = 1000,
    ) -> list[Vec2]:
        sorted_verts = LosSystem.get_sorted_verts(gs, spotter_pos)
        visible_points: list[Vec2] = []
        for vert in sorted_verts:
            ray = (vert - spotter_pos).normalized() * range
            intersects = list(
                LosSystem.get(
                    gs=gs,
                    start=spotter_pos,
                    end=spotter_pos + ray,
                    mask=TerrainFeature.Flag.OPAQUE,
                )
            )
            if len(intersects) != 0:
                points = [intersect.point for intersect in intersects]
                points = LosSystem.sort_by_distance(points, spotter_pos)
                points = LosSystem.filter_new_points(points)
                for point in points:
                    LosSystem.add_point(visible_points, point)
            else:
                LosSystem.add_point(visible_points, spotter_pos + ray)

        return visible_points

    @staticmethod
    def get_sorted_verts(
        gs: GameState,
        spotter_pos: Vec2,
    ) -> list[Vec2]:
        verts: list[Vec2] = []
        for _, terrain, transform in gs.query(TerrainFeature, Transform):
            if (terrain.flag & TerrainFeature.Flag.OPAQUE) == 0:
                continue
            verts += LinearTransform.apply(terrain.vertices, transform)
        sorted_verts = LosSystem.sort_by_angle(verts, spotter_pos)
        return sorted_verts

    @staticmethod
    def filter_new_points(verts: list[Vec2]) -> list[Vec2]:

        return verts

    @staticmethod
    def add_point(visible_points: list[Vec2], new_point: Vec2) -> None:
        if len(visible_points) >= 2:
            a = visible_points[-2]
            b = visible_points[-1]
            c = new_point

            # Vector cross product (2D scalar) to test collinearity
            ab = b - a
            ac = c - a
            cross = ab.x * ac.y - ab.y * ac.x

            if abs(cross) < 1e-9:  # nearly collinear
                visible_points[-1] = new_point
                return

        visible_points.append(new_point)

    @staticmethod
    def sort_by_angle(
        verts: list[Vec2],
        spotter_pos: Vec2,
    ) -> list[Vec2]:
        def angle_from_spotter(v: Vec2) -> float:
            # Vector from spotter_pos to vertex
            rel = v - spotter_pos
            # Compute angle relative to +x axis (0 radians)
            theta = math.atan2(rel.y, rel.x)
            # Normalize to [0, 2π)
            if theta < 0:
                theta += 2 * math.pi
            return theta

        return sorted(verts, key=angle_from_spotter)

    @staticmethod
    def sort_by_distance(
        verts: list[Vec2],
        spotter_pos: Vec2,
    ) -> list[Vec2]:
        def distance_from_spotter(v: Vec2) -> float:
            return (v - spotter_pos).length()

        return sorted(verts, key=distance_from_spotter)

    @staticmethod
    def get(
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
