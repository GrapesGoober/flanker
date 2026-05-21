from flanker_core.gamestate import GameState
from flanker_core.models.components import TerrainFeature, Transform
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.los_system import LosSystem
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

    @staticmethod
    def expand_waypoints_interrupt(
        gs: GameState,
        initial_waypoints: list[Vec2],
        iterations: int,
    ) -> list[Vec2]:
        """
        Given a list of waypoints, expand and create more waypoints
        representing move interrupt candidates.
        """
        los_system = gs.get(LosSystem)

        waypoints_los_polygon: dict[Vec2, list[Vec2]] = {}
        waypoints = set(initial_waypoints)

        terrain_vertices: list[list[Vec2]] = []
        for _, terrain, transform in gs.query(TerrainFeature, Transform):
            vertices = LinearTransform.apply(terrain.vertices, transform)
            if terrain.is_closed_loop:
                vertices.append(vertices[0])
            terrain_vertices.append(vertices)

        for _ in range(iterations):
            processed_pair: list[tuple[Vec2, Vec2]] = []
            intersects: list[Vec2] = []
            for waypoint_a in waypoints:
                for waypoint_b in waypoints:
                    if waypoint_a == waypoint_b:
                        continue
                    if (waypoint_a, waypoint_b) in processed_pair:
                        continue
                    if (waypoint_b, waypoint_a) in processed_pair:
                        continue
                    processed_pair.append((waypoint_a, waypoint_b))

                    # Check against all terrain for intersections
                    for terrain in terrain_vertices:
                        intersects += IntersectGetter.get_intersects(
                            line=(waypoint_a, waypoint_b),
                            polyline=terrain,
                        )

                    # Check against all other waypoints for interrupts
                    for other_waypoint in waypoints:
                        if other_waypoint in [waypoint_a, waypoint_b]:
                            continue

                        if other_waypoint not in waypoints_los_polygon:
                            waypoints_los_polygon[other_waypoint] = (
                                los_system.get_los_polygon(gs, other_waypoint)
                            )
                        los_polygon = waypoints_los_polygon[other_waypoint]

                        # For now, consider polygon-edge as interrupts.
                        # Let's ignore FOV constraints for now.
                        intersects += IntersectGetter.get_intersects(
                            line=(waypoint_a, waypoint_b),
                            polyline=los_polygon,
                        )
            waypoints |= set(intersects)
        return list(waypoints)
