import math
from typing import Iterable

from core.components import CombatUnit, TerrainFeature, Transform
from core.gamestate import GameState
from core.systems.intersect_system import IntersectSystem
from core.utils.intersect_getter import IntersectGetter
from core.utils.linear_transform import LinearTransform
from core.utils.vec2 import Vec2
from dataclasses import dataclass


@dataclass
class TerrainIntersection:
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
        jitter_size: float = 1e-6,  # Smaller than this will break t-u bezier checks
    ) -> list[Vec2]:
        """Returns a polygon representing the LOS from a spotter position."""
        verts = LosSystem._sort_verts_by_angle(gs, spotter_pos)
        visible_points: list[Vec2] = []
        for vert in verts:
            direction = (vert - spotter_pos).normalized()
            # TODO: Remove radius, cast towards the bounding box instead
            ray = direction * radius
            # Instead of casting one ray, casts two rays slightly to the left and right.
            # This prevents boundary sensitivity when casting rays at the vertices.
            jitter = direction.rotated(1.5708) * jitter_size
            left_point = spotter_pos - jitter
            right_point = spotter_pos + jitter
            for point in [left_point, right_point]:
                intersects = list(
                    LosSystem._get_terrain_intersects(
                        gs=gs,
                        start=point,
                        end=point + ray,
                        mask=TerrainFeature.Flag.OPAQUE,
                    )
                )
                # Choose which point from the intersects to append
                if intersects:
                    intersects = LosSystem._sort_intersects_by_distance(
                        intersects, spotter_pos
                    )
                    # Use the second intersection point to allow see-into terrain
                    if len(intersects) > 1:
                        new_point = intersects[1].point
                    else:
                        new_point = intersects[0].point
                else:  # No intersects, use fallback point using the ray
                    new_point = spotter_pos + ray

                # If the new point is close enough to the target vertex,
                # assume that the point is aimed there and lands close enough
                if (new_point - vert).length() < 1e-3:
                    new_point = vert
                # If points are colocated, don't append
                if visible_points and visible_points[-1] == new_point:
                    continue
                # If points are colinear, replace instead of append
                if LosSystem._is_colinear(visible_points, new_point):
                    visible_points[-1] = new_point
                    continue
                visible_points.append(new_point)

        return visible_points

    @staticmethod
    def _sort_verts_by_angle(
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
    def _is_colinear(previous_points: list[Vec2], new_point: Vec2) -> bool:
        """Returns whether points are colinear from the previous other points."""
        if len(previous_points) >= 2:
            a = previous_points[-2]
            b = previous_points[-1]
            c = new_point
            ab = b - a
            ac = c - a
            cross = ab.cross(ac)
            if abs(cross) < 1e-9:
                previous_points[-1] = new_point
                return True

        return False

    @staticmethod
    def _sort_intersects_by_distance(
        verts: list[TerrainIntersection],
        spotter_pos: Vec2,
    ) -> list[TerrainIntersection]:
        """Sorts a list of intersection by distance from spotter."""

        def distance_from_spotter(v: TerrainIntersection) -> float:
            return (v.point - spotter_pos).length()

        return sorted(verts, key=distance_from_spotter)

    @staticmethod
    def _get_terrain_intersects(
        gs: GameState,
        start: Vec2,
        end: Vec2,
        mask: int = -1,
    ) -> Iterable[TerrainIntersection]:
        """Yields intersections between the line segment and terrain."""
        for id, terrain, transform in gs.query(TerrainFeature, Transform):
            if terrain.flag & mask:
                vertices = LinearTransform.apply(terrain.vertices, transform)
                if terrain.is_closed_loop:
                    vertices.append(vertices[0])
                    # Ignore the terrain entity if the spotter is inside it,
                    # this allows spotter to see-out of a terrain
                    if IntersectGetter.is_inside(start, vertices):
                        # This rule doesn't apply to boundary terrain
                        if (terrain.flag & TerrainFeature.Flag.BOUNDARY) == 0:
                            continue

                points = IntersectGetter.get_intersects(
                    line=(start, end),
                    vertices=vertices,
                )
                for point in points:
                    yield TerrainIntersection(point, terrain, id)
