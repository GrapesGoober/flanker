import math
from dataclasses import dataclass
from typing import Callable, Iterable
from uuid import UUID

from flanker_core.gamestate import GameState
from flanker_core.models.components import TerrainFeature, Transform
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.terrain_system import TerrainSystem
from flanker_core.utils.intersect_getter import IntersectGetter
from flanker_core.utils.linear_transform import LinearTransform
from flanker_core.utils.reachability_polygon import (
    Obstacle,
    ObstacleIntersection,
    ReachabilityPolygon,
)

FOV_DEGREE = 90


@dataclass
class _Terrain:
    """Represents a prepared terrain ready for LOS."""

    terrain_id: UUID
    vertices: list[Vec2]


@dataclass
class _LosCacheComponent:
    los_polygon_by_point: dict[Vec2, list[Vec2]]
    fov_polygon_by_point: dict[tuple[Vec2, float], list[Vec2]]


class LosSystemOverrides:
    """
    Add these to game state to override LOS system with new logic.
    """

    @dataclass
    class HasLos:
        method: Callable[
            [GameState, Vec2, Vec2],
            bool,
        ]

    @dataclass
    class GetLosFromLine:
        method: Callable[
            [GameState, UUID, tuple[Vec2, Vec2]],
            Vec2 | None,
        ]

    @dataclass
    class GetLosPolygon:
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
        for _, override in gs.query(LosSystemOverrides.HasLos):
            return override.method(gs, spotter_pos, target_pos)

        # Count each intersects to not see through terrain
        intersects = TerrainSystem.get_intersect(
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
        for _, override in gs.query(LosSystemOverrides.GetLosFromLine):
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
        """
        Returns a polygon representing the LOS from a spotter position.
        Does not consider the FOV of the spotter.
        """

        # Use the override if exists
        for _, override in gs.query(LosSystemOverrides.GetLosPolygon):
            return override.method(gs, spotter_pos)

        # If already exists in cache, no need to recalculate
        if ent := gs.query(_LosCacheComponent):
            _, cache = ent[0]
        else:
            gs.add_entity(cache := _LosCacheComponent({}, {}))
        if spotter_pos in cache.los_polygon_by_point:
            return cache.los_polygon_by_point[spotter_pos]

        polygon = LosSystem._compute_los_polygon(gs, spotter_pos)
        cache.los_polygon_by_point[spotter_pos] = polygon
        return polygon

    @staticmethod
    def _compute_los_polygon(
        gs: GameState,
        spotter_pos: Vec2,
    ) -> list[Vec2]:
        """Generates a new LOS polygon."""

        terrains = LosSystem._get_terrains(gs, spotter_pos)
        obstacles: list[Obstacle[UUID]] = []
        for terrain in terrains:
            obstacles.append(
                Obstacle(
                    polyline=terrain.vertices,
                    metadata=terrain.terrain_id,
                )
            )

        def criteria(
            intersects: list[ObstacleIntersection[UUID]],
        ) -> Vec2:
            # Selects the second point to allow see-into terrain
            if len(intersects) > 1:
                new_point = intersects[1].point
            else:
                new_point = intersects[0].point
            return new_point

        return ReachabilityPolygon.get_polygon(
            center_point=spotter_pos,
            obstacles=obstacles,
            criteria=criteria,
        )

    # TODO reuse this from utils?
    @staticmethod
    def _sort_verts_by_angle(
        spotter_pos: Vec2,
        verts: list[Vec2],
    ) -> list[Vec2]:
        """Get all terrain vertices sorted by angle."""

        def angle_from_spotter(v: Vec2) -> float:
            rel = v - spotter_pos
            theta = math.atan2(rel.y, rel.x)
            if theta < 0:
                theta += 2 * math.pi
            return theta

        return sorted(verts, key=angle_from_spotter)

    # TODO recycle this for `has_los` too
    @staticmethod
    def _get_terrains(
        gs: GameState,
        spotter_pos: Vec2,
        mask: int = TerrainFeature.Flag.OPAQUE,
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
                yield _Terrain(terrain_id=id, vertices=vertices)
