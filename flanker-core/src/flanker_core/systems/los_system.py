import math
from dataclasses import dataclass
from typing import Iterable

from flanker_core.gamestate import GameState
from flanker_core.models.components import FireControls, TerrainFeature, Transform
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.intersect_system import IntersectSystem
from flanker_core.utils.intersect_getter import IntersectGetter
from flanker_core.utils.linear_transform import LinearTransform


@dataclass
class _TerrainIntersection:
    """Represents intersection between line and terrain feature."""

    point: Vec2
    terrain: TerrainFeature
    terrain_id: int


@dataclass
class _Terrain:
    """Represents a prepared terrain ready for LOS."""

    terrain_id: int
    terrain_feature: TerrainFeature
    vertices: list[Vec2]


class LosSystem:
    """Static system class for checking Line-of-Sight (LOS) against terrain."""

    @staticmethod
    def check(gs: GameState, spotter_pos: Vec2, target_pos: Vec2) -> bool:
        """Returns `True` if entity `spotter_id` can see position `target_pos`."""

        intersects = IntersectSystem.get(
            gs=gs,
            start=spotter_pos,
            end=target_pos,
            mask=TerrainFeature.Flag.OPAQUE,
        )

        # Can see into one other terrain polygon
        passed_one_terrain = False
        for intersect in intersects:
            # Doesn't count spotter's terrain
            terrain_id = intersect.terrain_id
            terrain = gs.get_component(terrain_id, TerrainFeature)
            terrain_transform = gs.get_component(terrain_id, Transform)
            vertices = LinearTransform.apply(terrain.vertices, terrain_transform)
            if terrain.is_closed_loop:
                vertices.append(vertices[0])
                if IntersectGetter.is_inside(point=spotter_pos, polygon=vertices):
                    continue

            if not passed_one_terrain:
                passed_one_terrain = True
                continue
            # Can only see into one polygon
            if passed_one_terrain:
                return False
        return True

    @staticmethod
    def _apply_fov_to_polygon(
        polyline: list[Vec2],
        center_point: Vec2,
        heading_degree: float,
        fov_degree: int = 90,  # Hardcoded FOV for now.
        radius: float = 1000,
    ) -> list[Vec2]:
        """Applies FOV cone to LOS polygon to create a smaller LOS code."""

        # Create some rays that defines this FOV cone
        heading_rad = math.radians(heading_degree)
        forward_ray: Vec2 = Vec2(1, 0).rotated(heading_rad)
        half_angle_rad = math.radians(fov_degree / 2)
        left_ray: Vec2 = center_point + (forward_ray * radius).rotated(-half_angle_rad)
        right_ray: Vec2 = center_point + (forward_ray * radius).rotated(half_angle_rad)
        left_point: Vec2 = IntersectGetter.get_intersects(
            line=(center_point, left_ray), polyline=polyline
        )[0]
        right_point: Vec2 = IntersectGetter.get_intersects(
            line=(center_point, right_ray), polyline=polyline
        )[0]

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
            a: Vec2 = forward_ray
            b: Vec2 = direction.normalized()
            if a.dot(b) >= threshold_rad:
                new_los.append(vertex)

        # Add left points and right points back to the list
        # to represent the cut FOV edges.
        new_los.append(left_point)
        new_los.append(right_point)
        new_los.append(center_point - forward_ray * 1e-9)
        new_los = LosSystem._sort_verts_by_angle(center_point, new_los)
        new_los.append(new_los[0])  # Loop back to a closed polyline
        return new_los

    @staticmethod
    def update_los_polygon(
        gs: GameState,
        unit_id: int,
    ) -> None:
        """Updates a unit's fire controls with a new LOS polygon."""
        transform = gs.get_component(unit_id, Transform)
        full_polygon = LosSystem.get_los_polygon(
            gs=gs,
            spotter_pos=transform.position,
        )
        fov_polygon = LosSystem._apply_fov_to_polygon(
            polyline=full_polygon,
            center_point=transform.position,
            heading_degree=transform.degrees,
        )
        fire_controls = gs.get_component(unit_id, FireControls)
        fire_controls.los_polygon = fov_polygon

    @staticmethod
    def get_los_polygon(
        gs: GameState,
        spotter_pos: Vec2,
        radius: float = 1000,
        jitter_size: float = 1e-6,  # Smaller than this will break t-u bezier checks
    ) -> list[Vec2]:
        """Returns a polygon representing the LOS from a spotter position."""
        terrains = list(
            LosSystem._get_terrain_vertices(
                gs,
                spotter_pos,
                mask=TerrainFeature.Flag.OPAQUE,
            )
        )
        terrain_verts = [vert for t in terrains for vert in t.vertices]
        verts = LosSystem._sort_verts_by_angle(spotter_pos, terrain_verts)
        visible_points: list[Vec2] = []
        for vert in verts:
            direction = (vert - spotter_pos).normalized()
            ray = direction * radius
            # Instead of casting one ray, casts two rays slightly to the left and right.
            # This prevents boundary sensitivity when casting rays at the vertices.
            jitter = direction.rotated(1.5708) * jitter_size
            left_point = spotter_pos - jitter
            right_point = spotter_pos + jitter
            for point in [left_point, right_point]:
                intersects = list(
                    LosSystem._get_terrain_intersects(
                        line=(point, point + ray),
                        terrains=terrains,
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

        visible_points.append(visible_points[0])
        return visible_points

    @staticmethod
    def _sort_verts_by_angle(
        spotter_pos: Vec2,
        verts: list[Vec2],
    ) -> list[Vec2]:
        """Get all terrain vertices sorted by angle."""

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
                return True

        return False

    @staticmethod
    def _sort_intersects_by_distance(
        intersects: list[_TerrainIntersection],
        spotter_pos: Vec2,
    ) -> list[_TerrainIntersection]:
        """Sorts a list of intersection by distance from spotter."""

        def distance_from_spotter(v: _TerrainIntersection) -> float:
            return (v.point - spotter_pos).length()

        return sorted(intersects, key=distance_from_spotter)

    @staticmethod
    def _get_terrain_intersects(
        line: tuple[Vec2, Vec2],
        terrains: list[_Terrain],
    ) -> Iterable[_TerrainIntersection]:
        """Yields intersections between the line segment and terrain."""
        for terrain in terrains:
            points = IntersectGetter.get_intersects(
                line=line,
                polyline=terrain.vertices,
            )
            for point in points:
                yield _TerrainIntersection(
                    point,
                    terrain.terrain_feature,
                    terrain.terrain_id,
                )

    @staticmethod
    def _get_terrain_vertices(
        gs: GameState,
        spotter_pos: Vec2,
        mask: int = -1,
    ) -> Iterable[_Terrain]:
        """Yields only relevant terrains and its transformed vertices."""
        for id, terrain, transform in gs.query(TerrainFeature, Transform):
            if terrain.flag & mask:
                vertices = LinearTransform.apply(terrain.vertices, transform)
                if terrain.is_closed_loop:
                    vertices.append(vertices[0])
                    # Ignore the terrain entity if the spotter is inside it,
                    # this allows spotter to see-out of a terrain
                    if (
                        IntersectGetter.is_inside(spotter_pos, vertices)
                        # This rule doesn't apply to boundary terrain
                        and (terrain.flag & TerrainFeature.Flag.BOUNDARY) == 0
                    ):
                        continue
                yield _Terrain(id, terrain, vertices)
