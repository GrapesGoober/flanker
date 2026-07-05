import math
from dataclasses import dataclass
from typing import Callable, Iterable
from uuid import UUID

from flanker_core.gamestate import GameState
from flanker_core.models.components import TerrainFeature, Transform
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.intersect_system import IntersectSystem
from flanker_core.utils.intersect_getter import IntersectGetter
from flanker_core.utils.linear_transform import LinearTransform

FOV_DEGREE = 90


@dataclass
class _TerrainIntersection:
    """Represents intersection between line and terrain feature."""

    point: Vec2
    terrain: TerrainFeature
    terrain_id: UUID


@dataclass
class _Terrain:
    """Represents a prepared terrain ready for LOS."""

    terrain_id: UUID
    terrain_feature: TerrainFeature
    vertices: list[Vec2]


@dataclass
class _LosCacheComponent:
    los_polygon_by_point: dict[Vec2, list[Vec2]]
    fov_polygon_by_point: dict[tuple[Vec2, float], list[Vec2]]


@dataclass
class HasLosOverrideComponent:
    method: Callable[
        [GameState, Vec2, Vec2],
        bool,
    ]


@dataclass
class GetLosFromLineOverrideComponent:
    method: Callable[
        [GameState, UUID, tuple[Vec2, Vec2]],
        Vec2 | None,
    ]


@dataclass
class GetLosPolygonOverrideComponent:
    method: Callable[
        [GameState, Vec2],
        list[Vec2],
    ]


class LosSystem:
    """Static system class for checking Line-of-Sight (LOS) against terrain."""

    @staticmethod
    def in_fov(
        spotter_transform: Transform,
        target_pos: Vec2,
        fov: float = FOV_DEGREE,
    ) -> bool:
        """
        Util method returns `True` the target position `target_pos`
        is in FOV cone of spotter position `spotter_transform`.
        """

        # Direction the spotter is facing
        heading_rad = math.radians(spotter_transform.degrees)
        forward_dir: Vec2 = Vec2(1, 0).rotated(heading_rad)

        # Direction to target
        to_target = (target_pos - spotter_transform.position).normalized()

        # Dot product -> angle check
        dot = forward_dir.dot(to_target)

        # cos(theta) comparison (avoid expensive acos)
        half_fov_rad = math.radians(fov / 2)
        return dot >= math.cos(half_fov_rad)

    @staticmethod
    def has_los(
        gs: GameState,
        spotter_pos: Vec2,
        target_pos: Vec2,
    ) -> bool:
        """
        Returns `True` if position `spotter_pos` has LOS to
        position `target_pos`. Does not check for FOV.
        """

        # Use the override if exists
        for _, override in gs.query(HasLosOverrideComponent):
            return override.method(gs, spotter_pos, target_pos)

        # Count each intersects to not see through terrain
        intersects = IntersectSystem.get(
            gs=gs,
            start=spotter_pos,
            end=target_pos,
            mask=TerrainFeature.Flag.OPAQUE,
        )
        passed_one_terrain = False
        for intersect in intersects:
            # Doesn't count spotter's terrain
            terrain_id = intersect.terrain_id
            terrain = gs.get_component(terrain_id, TerrainFeature)
            terrain_transform = gs.get_component(terrain_id, Transform)
            vertices = LinearTransform.apply(
                vec_list=terrain.vertices,
                transform=terrain_transform,
            )
            if terrain.is_closed_loop:
                vertices.append(vertices[0])
                if IntersectGetter.is_inside(
                    point=spotter_pos,
                    polygon=vertices,
                ):
                    continue

            if not passed_one_terrain:
                passed_one_terrain = True
                continue
            # Can only see into one polygon
            if passed_one_terrain:
                return False
        return True

    @staticmethod
    def get_los_from_line(
        gs: GameState,
        spotter_id: UUID,
        line: tuple[Vec2, Vec2],
    ) -> Vec2 | None:
        """
        Returns an eariliest point position, if exists, along `line` that
        has a valid LOS to the entity `spotter_id`. This considers FOV.
        """

        # Use the override if exists
        for _, override in gs.query(GetLosFromLineOverrideComponent):
            return override.method(gs, spotter_id, line)

        interrupt_pos: Vec2 | None = None

        spotter_transform = gs.get_component(spotter_id, Transform)

        # If already exists in cache, no need to recalculate
        if ent := gs.query(_LosCacheComponent):
            _, cache = ent[0]
        else:
            gs.add_entity(cache := _LosCacheComponent({}, {}))

        cache_key: tuple[Vec2, float] = (
            spotter_transform.position,
            spotter_transform.degrees,
        )
        if cache_key in cache.fov_polygon_by_point:
            fov_polygon = cache.fov_polygon_by_point[cache_key]
        else:
            los_polygon = LosSystem.get_los_polygon(
                gs=gs,
                spotter_pos=spotter_transform.position,
            )
            fov_polygon = LosSystem.apply_fov_to_polygon(
                polyline=los_polygon,
                center_point=spotter_transform.position,
                heading_degree=spotter_transform.degrees,
            )
            cache.fov_polygon_by_point[cache_key] = fov_polygon

        # If the first point is inside, ignore any intersections and
        # return the first point right away.
        if IntersectGetter.is_inside(
            point=line[0],
            polygon=fov_polygon,
        ):
            interrupt_pos = line[0]

        # The first point is outside, thus only care about intersection
        elif intersects := IntersectGetter.get_intersects(
            line=(line[0], line[1]),
            polyline=fov_polygon,
        ):
            earliest_point = min(
                intersects,
                key=lambda point: (line[0] - point).length(),
            )
            # Add a tiny offset to prevent coordinate from sitting
            # precisely on LOS polygon edge.
            # This reduces floating point sensitivity.
            line_direction = line[1] - line[0]
            offset = line_direction * 1e-12
            interrupt_pos = earliest_point + offset

        return interrupt_pos

    @staticmethod
    def apply_fov_to_polygon(
        polyline: list[Vec2],
        center_point: Vec2,
        heading_degree: float,
        fov_degree: int = FOV_DEGREE,
        radius: float = 1000,
    ) -> list[Vec2]:
        """Applies FOV cone to LOS polygon to create a smaller LOS cone."""

        # Create some rays that defines this FOV cone
        heading_rad = math.radians(heading_degree)
        forward_direction: Vec2 = Vec2(1, 0).rotated(heading_rad)
        forward_ray = forward_direction * radius
        half_angle_rad = math.radians(fov_degree / 2)
        left_ray: Vec2 = center_point + forward_ray.rotated(half_angle_rad)
        right_ray: Vec2 = center_point + forward_ray.rotated(-half_angle_rad)

        # Choose the two first intersection points of this FOV cone
        left_point = min(
            IntersectGetter.get_intersects(
                line=(center_point, left_ray), polyline=polyline
            ),
            key=lambda point: (center_point - point).length(),
        )
        right_point = min(
            IntersectGetter.get_intersects(
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
        new_los = LosSystem._sort_verts_by_angle(center_point, new_los)
        new_los.append(new_los[0])  # Loop back to a closed polyline
        return new_los

    @staticmethod
    def get_los_polygon(
        gs: GameState,
        spotter_pos: Vec2,
        radius: float = 1000,
        jitter_size: float = 1e-6,  # Smaller than this will break t-u bezier checks
    ) -> list[Vec2]:
        """Returns a polygon representing the LOS from a spotter position."""

        # Use the override if exists
        for _, override in gs.query(GetLosPolygonOverrideComponent):
            return override.method(gs, spotter_pos)

        # If already exists in cache, no need to recalculate
        if ent := gs.query(_LosCacheComponent):
            _, cache = ent[0]
        else:
            gs.add_entity(cache := _LosCacheComponent({}, {}))
        if spotter_pos in cache.los_polygon_by_point:
            return cache.los_polygon_by_point[spotter_pos]

        terrains = list(
            LosSystem._get_terrain_vertices(
                gs,
                spotter_pos,
                mask=TerrainFeature.Flag.OPAQUE,
            )
        )
        terrain_verts = [vert for t in terrains for vert in t.vertices]
        verts = LosSystem._sort_verts_by_angle(spotter_pos, terrain_verts)
        los_polygon: list[Vec2] = []
        for vert in verts:
            direction = (vert - spotter_pos).normalized()
            ray = direction * radius
            # Instead of casting one ray, casts two rays slightly to the left and right.
            # This prevents boundary sensitivity when casting rays at the vertices.
            jitter = direction.rotated(1.5708) * jitter_size
            left_point = spotter_pos - jitter
            right_point = spotter_pos + jitter
            for point in [left_point, right_point]:
                intersects = sorted(
                    LosSystem._get_terrain_intersects(
                        line=(point, point + ray),
                        terrains=terrains,
                    ),
                    key=lambda i: (i.point - spotter_pos).length(),
                )
                # Choose which point from the intersects to append
                if intersects:
                    # Selects the second point to allow see-into terrain
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
                if los_polygon and los_polygon[-1] == new_point:
                    continue
                # If points are colinear, replace instead of append
                if LosSystem._is_colinear(los_polygon, new_point):
                    los_polygon[-1] = new_point
                    continue
                los_polygon.append(new_point)

        los_polygon.append(los_polygon[0])
        cache.los_polygon_by_point[spotter_pos] = los_polygon
        return los_polygon

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
        """Yields unsorted intersections between the line segment and terrain."""
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
