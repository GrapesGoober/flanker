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
        Returns a list of angles where the aspect changes, from a given position.
        An aspect change is when a small change in angle leads to significant
        change in what the terrain is visible.
        """

        obstacles = list(LosSystem.get_obstacles(gs, transform.position))
        vertices = PolygonUtils.get_vertices_from_obstacles(obstacles)
        aspects: list[float] = []

        for vertex in vertices:
            if AiAspectBoundaryService._is_aspect_boundary(
                vertex,
                transform.position,
                obstacles,
            ):
                aspects.append(transform.position.angle_to(vertex) % 360)

        return aspects

    @staticmethod
    def _is_aspect_boundary(
        vertex: Vec2,
        spotter_pos: Vec2,
        obstacles: list[Obstacle[UUID]],
    ) -> bool:
        """
        Checks whether the given vertex is an aspect boundary.
        """

        direction = (vertex - spotter_pos).normalized()
        if direction.length() == 0:
            return False

        jitter = direction.rotated(90) * 1e-6
        hit_obstacle_ids = [
            AiAspectBoundaryService._get_first_hit_obstacle_id(
                cast_from,
                direction,
                spotter_pos,
                obstacles,
            )
            for cast_from in (spotter_pos - jitter, spotter_pos + jitter)
        ]
        return hit_obstacle_ids[0] != hit_obstacle_ids[1]

    @staticmethod
    def _get_first_hit_obstacle_id(
        cast_from: Vec2,
        direction: Vec2,
        spotter_pos: Vec2,
        obstacles: list[Obstacle[UUID]],
    ) -> UUID | None:
        """
        Casts a ray in the given direction and returns the closest obstacle.
        """

        # Track each intersected obstacle ID and its distance from the spotter.
        intersection_distances: list[tuple[float, UUID]] = [
            ((intersection_point - spotter_pos).length(), obstacle.metadata)
            for obstacle in obstacles
            for intersection_point in IntersectUtils.get_intersects(
                line=(cast_from, cast_from + direction * 1000),
                polyline=obstacle.polyline,
            )
        ]
        if not intersection_distances:
            return None

        # Grab the obstacle with the nearest intersection.
        nearest_intersection = min(
            intersection_distances,
            key=lambda intersection: intersection[0],
        )
        return nearest_intersection[1]
