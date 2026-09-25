import random

from flanker_ai.config_models import PointsConfig
from flanker_core.gamestate import GameState
from flanker_core.models.components import MapBoundary
from flanker_core.models.vec2 import Vec2
from flanker_core.utils.polygon_utils import PolygonUtils


class AiPointsInitializeService:
    """
    AI state-agnositic service that generates initial set of waypoints.
    This does not perform any analysis.
    """

    @staticmethod
    def get_initial_points(
        gs: GameState,
        config: PointsConfig.ALL,
    ) -> list[Vec2]:
        """Creates initial points given the config."""

        waypoints: list[Vec2]
        match config:
            case PointsConfig.HandDrawn():
                waypoints = config.points
            case PointsConfig.Grid():
                waypoints = AiPointsInitializeService.get_grid_coordinates(
                    gs=gs,
                    spacing=config.spacing,
                    offset=config.offset,
                )
            case PointsConfig.Random():
                waypoints = AiPointsInitializeService.get_random_coordinates(
                    gs=gs,
                    count=config.count,
                )

        return waypoints

    @staticmethod
    def get_grid_coordinates(
        gs: GameState,
        spacing: float,
        offset: float,
    ) -> list[Vec2]:
        boundary_vertices = AiPointsInitializeService._get_map_boundary(gs)
        # Generates waypoints at spacing within boundary
        min_x = min(v.x for v in boundary_vertices) + offset
        max_x = max(v.x for v in boundary_vertices)
        min_y = min(v.y for v in boundary_vertices) + offset
        max_y = max(v.y for v in boundary_vertices)
        points: list[Vec2] = []
        y = min_y
        while y <= max_y:
            x = min_x
            while x <= max_x:
                p = Vec2(x, y)

                # Keep only points inside polygon
                if PolygonUtils.is_inside(p, boundary_vertices):
                    points.append(p)

                x += spacing
            y += spacing
        return points

    @staticmethod
    def get_random_coordinates(
        gs: GameState,
        count: int,
    ) -> list[Vec2]:
        boundary_vertices = AiPointsInitializeService._get_map_boundary(gs)
        min_x = int(min(v.x for v in boundary_vertices))
        max_x = int(max(v.x for v in boundary_vertices))
        min_y = int(min(v.y for v in boundary_vertices))
        max_y = int(max(v.y for v in boundary_vertices))

        move_candidates: list[Vec2] = []
        for _ in range(count):
            rand_x = random.randrange(min_x, max_x)
            rand_y = random.randrange(min_y, max_y)
            move_candidate = Vec2(rand_x, rand_y)
            if not PolygonUtils.is_inside(
                point=move_candidate,
                polygon=boundary_vertices,
            ):
                continue
            move_candidates.append(move_candidate)
        return move_candidates

    @staticmethod
    def _get_map_boundary(gs: GameState) -> list[Vec2]:
        # Grab the map boundary
        boundary_vertices: list[Vec2] = [
            vertex
            for _, boundary in gs.query(MapBoundary)
            for vertex in boundary.vertices
        ]
        boundary_vertices.append(boundary_vertices[0])
        if len(boundary_vertices) < 3:
            raise ValueError("Can't generate coordinates; map boundary missing!")
        return boundary_vertices
