from flanker_core.gamestate import GameState
from flanker_core.models.components import TerrainFeature, Transform
from flanker_core.models.vec2 import Vec2
from flanker_core.utils.intersect_getter import IntersectGetter
from flanker_core.utils.linear_transform import LinearTransform


class WaypointsGeneratorService:
    """
    Waypoints-Graph service that generates a set of waypoint positions
    using in-game terrain. This is used by waypoints-state constructor
    to generate a waypoints graph.
    """

    @staticmethod
    def get_grid_coordinates(
        gs: GameState, spacing: float, offset: float
    ) -> list[Vec2]:

        # Grab the map boundary
        mask = TerrainFeature.Flag.BOUNDARY
        boundary_vertices: list[Vec2] = []
        for _, terrain, transform in gs.query(TerrainFeature, Transform):
            if terrain.flag & mask:
                boundary_vertices = LinearTransform.apply(
                    terrain.vertices,
                    transform,
                )
                if terrain.is_closed_loop:
                    boundary_vertices.append(boundary_vertices[0])

        if len(boundary_vertices) < 3:
            raise ValueError("Can't generate coordinates; boundary terrain missing!")

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
                if IntersectGetter.is_inside(p, boundary_vertices):
                    points.append(p)

                x += spacing
            y += spacing
        return points
