from uuid import UUID

from flanker_core.gamestate import GameState
from flanker_core.models.components import Transform
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.los_system import LosSystem
from flanker_core.utils.intersect_utils import IntersectUtils
from flanker_core.utils.polygon_utils import Obstacle, PolygonUtils


class AiAspectBoundaryService:

    @staticmethod
    def get_aspects_boundaries(
        gs: GameState,
        transform: Transform,
    ) -> list[float]:
        """
        Returns a list of aspect boundary angles of a given position.
        """

        obstacle_pairs = list(LosSystem.get_obstacles(gs, transform.position))
        obstacles = [
            Obstacle(polyline=vertices, metadata=terrain_id)
            for terrain_id, vertices in obstacle_pairs
        ]
        vertices = PolygonUtils.get_vertices_from_obstacles(obstacles)
        aspects: list[float] = []

        for vertex in vertices:
            if AiAspectBoundaryService._is_aspect_boundary(
                vertex,
                transform.position,
                obstacle_pairs,
            ):
                aspects.append(transform.position.angle_to(vertex) % 360)

        return aspects

    @staticmethod
    def _is_aspect_boundary(
        vertex: Vec2,
        spotter_pos: Vec2,
        obstacles: list[tuple[UUID, list[Vec2]]],
    ) -> bool:
        """
        Checks whether the given vertex is an aspect boundary.
        """

        direction = (vertex - spotter_pos).normalized()
        if direction.length() == 0:
            return False

        jitter = direction.rotated(90) * 1e-6
        hit_terrain_ids = [
            AiAspectBoundaryService._get_first_hit_terrain_id(
                cast_from,
                direction,
                spotter_pos,
                obstacles,
            )
            for cast_from in (spotter_pos - jitter, spotter_pos + jitter)
        ]
        return hit_terrain_ids[0] != hit_terrain_ids[1]

    @staticmethod
    def _get_first_hit_terrain_id(
        cast_from: Vec2,
        direction: Vec2,
        spotter_pos: Vec2,
        obstacles: list[tuple[UUID, list[Vec2]]],
    ) -> UUID | None:
        """
        Casts a ray in the given direction and returns the closest obstacle.
        """

        # Track each intersected terrain ID and their distance
        intersection_distances: list[tuple[float, UUID]] = [
            ((intersection_point - spotter_pos).length(), terrain_id)
            for terrain_id, polyline in obstacles
            for intersection_point in IntersectUtils.get_intersects(
                line=(cast_from, cast_from + direction * 1000),
                polyline=polyline,
            )
        ]
        if not intersection_distances:
            return None

        # Grab the terrain with the nearest intersect
        nearest_intersection = min(
            intersection_distances,
            key=lambda intersection: intersection[0],
        )
        return nearest_intersection[1]
