from dataclasses import dataclass
from typing import Callable, Iterable
from uuid import UUID

from flanker_core.gamestate import GameState
from flanker_core.models.components import TerrainFeature, Transform
from flanker_core.models.vec2 import Vec2
from flanker_core.utils.intersect_utils import IntersectUtils
from flanker_core.utils.polygon_utils import (
    Obstacle,
    ObstacleIntersection,
    PolygonUtils,
)
from flanker_core.utils.transform_utils import TransformUtils


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
    def in_fov(  # TODO This method feels like utils. Where should it be placed?
        spotter_transform: Transform,
        target_pos: Vec2,
        fov: float = 90,
    ) -> bool:
        """
        Util method returns `True` the target position `target_pos`
        is in FOV cone of spotter position `spotter_transform`.
        """
        target_angle = spotter_transform.position.angle_to(target_pos)

        # Wraps around to be in range [-180, 180]
        angle_diff = (target_angle - spotter_transform.degrees + 180) % 360 - 180

        return abs(angle_diff) <= fov / 2

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

        # Use the override if exists.
        for _, override in gs.query(LosSystemOverrides.HasLos):
            return override.method(gs, spotter_pos, target_pos)

        # Check each intersection; allow see into and out-from terrain.
        passed_one_terrain = False
        for _, vertices in LosSystem._get_terrains(gs, spotter_pos):

            # Ignore spotter's terrain (allow to see out-from terrain)
            if PolygonUtils.is_inside(point=spotter_pos, polygon=vertices):
                continue

            # Count whether it passes one terrain
            for _ in IntersectUtils.get_intersects(
                line=(spotter_pos, target_pos),
                polyline=vertices,
            ):
                if passed_one_terrain:
                    return False
                passed_one_terrain = True

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

        # Reuse FOV polygon from cache
        fov_polygon: list[Vec2]
        if ent := gs.query(_LosCacheComponent):
            _, cache = ent[0]
        else:
            gs.add_entity(cache := _LosCacheComponent({}, {}))
        spotter_transform = gs.get_component(spotter_id, Transform)
        cache_key: tuple[Vec2, float] = (
            spotter_transform.position,
            spotter_transform.degrees,
        )
        if cache_key in cache.fov_polygon_by_point:
            fov_polygon = cache.fov_polygon_by_point[cache_key]
        else:  # Regenerate FOV polygon
            los_polygon = LosSystem.get_los_polygon(
                gs=gs,
                spotter_pos=spotter_transform.position,
            )
            fov_polygon = PolygonUtils.clip_by_fov_cone(
                polyline=los_polygon,
                center_point=spotter_transform.position,
                heading_degree=spotter_transform.degrees,
            )
            cache.fov_polygon_by_point[cache_key] = fov_polygon

        return LosSystem._get_line_fov_intersection(line, fov_polygon)

    @staticmethod
    def _get_line_fov_intersection(
        line: tuple[Vec2, Vec2],
        fov_polygon: list[Vec2],
    ) -> Vec2 | None:
        """
        Helper method for `get_los_from_line`.
        Returns the earliest intersection between a line and a FOV polygon.
        If the line already starts inside, return the starting point,
        otherwise returns the intersection.
        """
        # If the first point is inside, ignore any intersections and
        # return the first point right away.
        if PolygonUtils.is_inside(
            point=line[0],
            polygon=fov_polygon,
        ):
            return line[0]

        # The first point is outside, thus only care about intersection
        elif intersects := IntersectUtils.get_intersects(
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
            return earliest_point + offset

        return None

    @staticmethod
    def get_los_polygon(
        gs: GameState,
        spotter_pos: Vec2,
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

        # Not in cache; recompute LOS polygon
        polygon = LosSystem._compute_los_polygon(gs, spotter_pos)
        cache.los_polygon_by_point[spotter_pos] = polygon
        return polygon

    @staticmethod
    def _compute_los_polygon(
        gs: GameState,
        spotter_pos: Vec2,
    ) -> list[Vec2]:
        """Helper method for `get_los_polygon`. Generates a new LOS polygon."""

        terrains = LosSystem._get_terrains(gs, spotter_pos)
        obstacles: list[Obstacle[UUID]] = []
        for terrain_id, vertices in terrains:
            obstacles.append(
                Obstacle(
                    polyline=vertices,
                    metadata=terrain_id,
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

        return PolygonUtils.get_reachable_polygon(
            center_point=spotter_pos,
            obstacles=obstacles,
            criteria=criteria,
        )

    @staticmethod
    def _get_terrains(
        gs: GameState,
        spotter_pos: Vec2,
        mask: int = TerrainFeature.Flag.OPAQUE,
    ) -> Iterable[tuple[UUID, list[Vec2]]]:
        """Yields only relevant terrains and its transformed vertices."""
        for id, terrain, transform in gs.query(TerrainFeature, Transform):
            if terrain.flag & mask:
                vertices = TransformUtils.apply(terrain.vertices, transform)
                if terrain.is_closed_loop:
                    vertices.append(vertices[0])
                    # Ignore the terrain entity if the spotter is inside it,
                    # this allows spotter to see-out of a terrain
                    if (
                        PolygonUtils.is_inside(spotter_pos, vertices)
                        # This rule doesn't apply to boundary terrain
                        and (terrain.flag & TerrainFeature.Flag.BOUNDARY) == 0
                    ):
                        continue
                yield (id, vertices)
