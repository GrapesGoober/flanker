from dataclasses import dataclass
from typing import Callable, Iterable
from uuid import UUID

from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    FireControls,
    MapBoundary,
    TerrainFeature,
    Transform,
)
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
    def in_fov(
        gs: GameState,
        spotter_id: UUID,
        target_pos: Vec2,
    ) -> bool:
        """
        Returns whether the target's position is in spotter's FOV.
        """

        spotter_transform = gs.get_component(spotter_id, Transform)
        spotter_fire_controls = gs.get_component(spotter_id, FireControls)

        fov_degrees = spotter_fire_controls.fov_degrees
        if fov_degrees == None:
            return True

        target_angle = spotter_transform.position.angle_to(target_pos)

        # Wraps around to be in range [-180, 180]
        angle_diff = (target_angle - spotter_transform.degrees + 180) % 360 - 180

        return abs(angle_diff) <= fov_degrees / 2

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

        # Find all intersections towards the target point
        obstacle_intersections: list[ObstacleIntersection[UUID]] = []
        for obstacle in LosSystem.get_obstacles(gs, spotter_pos):
            intersections: list[Vec2] = IntersectUtils.get_intersects(
                line=(spotter_pos, target_pos),
                polyline=obstacle.polyline,
            )
            obstacle_intersections += [
                ObstacleIntersection(obstacle, intersection)
                for intersection in intersections
            ]

        obstacle_intersections = sorted(
            obstacle_intersections, key=lambda i: (i.point - spotter_pos).length()
        )

        # LOS is valid if there's no obstacles blocking it
        return LosSystem.get_furthest_los_point(obstacle_intersections) == None

    @staticmethod
    def get_los_from_line(
        gs: GameState,
        spotter_id: UUID,
        line_from: Vec2,
        line_to: Vec2,
    ) -> Vec2 | None:
        """
        Returns an eariliest point position, if exists, along `line` that
        has a valid LOS to the entity `spotter_id`. This considers FOV.
        """

        # Use the override if exists
        for _, override in gs.query(LosSystemOverrides.GetLosFromLine):
            return override.method(gs, spotter_id, (line_from, line_to))

        # Reuse the cache object if exists
        if ent := gs.query(_LosCacheComponent):
            _, cache = ent[0]
        else:
            gs.add_entity(cache := _LosCacheComponent({}, {}))

        # Create the cache key
        spotter_transform = gs.get_component(spotter_id, Transform)
        cache_key: tuple[Vec2, float] = (
            spotter_transform.position,
            spotter_transform.degrees,
        )

        # Try reusing the cached polygon
        fov_polygon: list[Vec2]
        if cache_key in cache.fov_polygon_by_point:
            fov_polygon = cache.fov_polygon_by_point[cache_key]

        # Polygon not exists, recalculate
        else:
            spotter_fire_controls = gs.get_component(spotter_id, FireControls)
            los_polygon = LosSystem.get_los_polygon(
                gs=gs,
                spotter_pos=spotter_transform.position,
            )
            if spotter_fire_controls.fov_degrees != None:
                fov_polygon = PolygonUtils.clip_by_fov_cone(
                    polyline=los_polygon,
                    center_point=spotter_transform.position,
                    heading_degree=spotter_transform.degrees,
                    fov_degrees=spotter_fire_controls.fov_degrees,
                )
            else:
                fov_polygon = los_polygon

            cache.fov_polygon_by_point[cache_key] = fov_polygon

        # Compute intersections and return
        return LosSystem._get_line_fov_intersection(line_from, line_to, fov_polygon)

    @staticmethod
    def _get_line_fov_intersection(
        line_from: Vec2,
        line_to: Vec2,
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
            point=line_from,
            polygon=fov_polygon,
        ):
            return line_from

        # The first point is outside, thus only care about intersection
        elif intersects := IntersectUtils.get_intersects(
            line=(line_from, line_to),
            polyline=fov_polygon,
        ):
            earliest_point = min(
                intersects,
                key=lambda point: (line_from - point).length(),
            )
            # Add a tiny offset to prevent coordinate from sitting
            # precisely on LOS polygon edge.
            # This reduces floating point sensitivity.
            line_direction = (line_to - line_from).normalized()
            offset = line_direction * 1e-6
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

        # Not in cache; recompute LOS polygon and update cache
        obstacles = list(LosSystem.get_obstacles(gs, spotter_pos))
        boundary_vertices = [
            vertex
            for _, boundary in gs.query(MapBoundary)
            for vertex in boundary.vertices
        ]
        los_polygon = PolygonUtils.get_reachable_polygon(
            center_point=spotter_pos,
            obstacles=obstacles,
            boundary_vertices=boundary_vertices,
            criteria=LosSystem.get_furthest_los_point,
        )
        cache.los_polygon_by_point[spotter_pos] = los_polygon
        return los_polygon

    @staticmethod
    def get_furthest_los_point(
        obstacle_intersections: list[ObstacleIntersection[UUID]],
    ) -> Vec2 | None:
        """
        Returns the furthest reaching LOS point from a given obstacles.
        This is the canonical LOS definition. The line intersects must
        be sorted from nearest to furthest.

        Note that since LOS is allowed to be seen out from a terrain,
        the obstacles must not include the terrain originating LOS.
        """

        # NOTE
        # Right now, assumes all intersections are normal terrains.
        # If there are different terrain types, then the metadata
        # terrain UUID needs to be used to determine LOS.
        # For now, just return the second point.

        # Allow see-into terrain, so select the second point.
        if len(obstacle_intersections) > 1:
            return obstacle_intersections[1].point

        # Only 1 intersects found doesn't count as LOS blocking.
        # Must be allowed to see through.
        elif len(obstacle_intersections) == 1:
            return None
        return None

    @staticmethod
    def get_obstacles(
        gs: GameState,
        spotter_pos: Vec2,
        mask: int = TerrainFeature.Flag.OPAQUE,
    ) -> Iterable[Obstacle[UUID]]:
        """Yields necessary obstacles for LOS game rule."""

        # Currently, only terrains are needed for obstacles.
        # This might not be the case as the game grows.
        for obstacle_id, terrain, transform in gs.query(TerrainFeature, Transform):
            if terrain.flag & mask:
                vertices = TransformUtils.apply(terrain.vertices, transform)
                if terrain.is_closed_loop:
                    vertices.append(vertices[0])
                    # Ignore the terrain entity if the spotter is inside it,
                    # this allows spotter to see-out of a terrain
                    if PolygonUtils.is_inside(spotter_pos, vertices):
                        continue
                yield Obstacle(polyline=vertices, metadata=obstacle_id)
