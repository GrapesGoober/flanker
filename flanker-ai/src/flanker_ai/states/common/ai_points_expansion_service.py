import random
from itertools import pairwise

from flanker_ai.config_models import PointsConfig
from flanker_ai.states.waypoints.waypoints_flag_service import WaypointsFlagService
from flanker_core.gamestate import GameState
from flanker_core.models.components import CombatUnit, TerrainFeature, Transform
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.los_system import LosSystem
from flanker_core.utils.intersect_getter import IntersectGetter
from flanker_core.utils.linear_transform import LinearTransform


class AiPointsExpansionService:
    """
    AI state-agnositic service that generates a set of point positions
    using in-game terrain. These points can be used as a discrete finite
    set of game-relavant coordinates.
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
    def get_random_coordinates(
        gs: GameState,
        count: int,
    ) -> list[Vec2]:
        boundary_vertices: list[Vec2] = []
        mask = TerrainFeature.Flag.BOUNDARY
        for _, terrain, transform in gs.query(TerrainFeature, Transform):
            if terrain.flag & mask:
                boundary_vertices = LinearTransform.apply(
                    terrain.vertices,
                    transform,
                )
                if terrain.is_closed_loop:
                    boundary_vertices.append(boundary_vertices[0])
        min_x = int(min(v.x for v in boundary_vertices))
        max_x = int(max(v.x for v in boundary_vertices))
        min_y = int(min(v.y for v in boundary_vertices))
        max_y = int(max(v.y for v in boundary_vertices))

        move_candidates: list[Vec2] = []
        for _ in range(count):
            rand_x = random.randrange(min_x, max_x)
            rand_y = random.randrange(min_y, max_y)
            move_candidate = Vec2(rand_x, rand_y)
            if not IntersectGetter.is_inside(
                point=move_candidate,
                polygon=boundary_vertices,
            ):
                continue
            move_candidates.append(move_candidate)
        return move_candidates

    @staticmethod
    def expand_waypoints_line_based(
        gs: GameState,
        initial_waypoints: list[Vec2],
        iterations: int,
        prune_iterations: int,
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

            # Loop through each waypoint pair to consider new
            # waypoint candidates to add. Note that this loop
            # can't add (mutate) directly to the waypoints set
            # while looping.
            new_waypoints: set[Vec2] = set()
            for waypoint_a in waypoints:
                for waypoint_b in waypoints:
                    intersects: list[Vec2] = []

                    # Ignore redundant pairs.
                    if waypoint_a == waypoint_b:
                        continue
                    if (waypoint_a, waypoint_b) in processed_pair:
                        continue
                    if (waypoint_b, waypoint_a) in processed_pair:
                        continue
                    processed_pair.append((waypoint_a, waypoint_b))

                    # Check against all terrain for intersections.
                    for terrain in terrain_vertices:
                        intersects += IntersectGetter.get_intersects(
                            line=(waypoint_a, waypoint_b),
                            polyline=terrain,
                        )

                    # Check against all other waypoints for interrupts.
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

                    # Loop through each subsegment on this waypoint line pair
                    # and add a new waypoint on the midpoint of subsegment.
                    points_on_line: list[Vec2] = list(set(intersects))
                    points_on_line.append(waypoint_a)
                    points_on_line.append(waypoint_b)
                    points_on_line.sort(key=lambda p: (waypoint_a - p).length())
                    for left_point, right_point in pairwise(points_on_line):
                        new_waypoints.add((left_point + right_point) / 2)

            # The 'or' operator |= is set concat
            waypoints |= new_waypoints

            # Prune some waypoints to reduce combinatorial explosion
            for _ in range(prune_iterations):
                waypoints = WaypointsFlagService.prune_waypoints(gs, waypoints)
        return list(waypoints)

    @staticmethod
    def get_points(gs: GameState, config: PointsConfig) -> list[Vec2]:

        waypoints: list[Vec2] = []

        # Use combat units as initial points
        for _, _, transform in gs.query(CombatUnit, Transform):
            waypoints.append(transform.position)

        # Creates initial points given the config
        initial_points_config = config.initial_points
        match initial_points_config:
            case PointsConfig.HandDrawnConfig():
                waypoints += initial_points_config.points
            case PointsConfig.GridConfig():
                waypoints += AiPointsExpansionService.get_grid_coordinates(
                    gs=gs,
                    spacing=initial_points_config.spacing,
                    offset=initial_points_config.offset,
                )
            case PointsConfig.RandomConfig():
                waypoints += AiPointsExpansionService.get_random_coordinates(
                    gs=gs,
                    count=initial_points_config.count,
                )
            case PointsConfig.VoronoiConfig():
                raise NotImplementedError()

        # Expands the points given the config
        expansion_config = config.expansion
        if expansion_config != None:
            match expansion_config.type:
                case "LineBased":
                    waypoints = AiPointsExpansionService.expand_waypoints_line_based(
                        gs=gs,
                        initial_waypoints=waypoints,
                        iterations=expansion_config.iterations,
                        prune_iterations=expansion_config.prune_iterations,
                    )
                case "Polygonal":
                    raise NotImplementedError()
        return waypoints
