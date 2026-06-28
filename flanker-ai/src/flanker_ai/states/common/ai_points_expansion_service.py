from itertools import pairwise

from flanker_ai.config_models import PointsConfig
from flanker_ai.states.common.ai_waypoints_initialize_service import (
    AiWaypointsInitializeService,
)
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
    def get_points(
        gs: GameState,
        config: PointsConfig,
    ) -> list[Vec2]:

        # Creates initial points given the config
        waypoints: list[Vec2]
        initial_points_config = config.initial_points
        match initial_points_config:
            case PointsConfig.HandDrawnConfig():
                waypoints = initial_points_config.points
            case PointsConfig.GridConfig():
                waypoints = AiWaypointsInitializeService.get_grid_coordinates(
                    gs=gs,
                    spacing=initial_points_config.spacing,
                    offset=initial_points_config.offset,
                )
            case PointsConfig.RandomConfig():
                waypoints = AiWaypointsInitializeService.get_random_coordinates(
                    gs=gs,
                    count=initial_points_config.count,
                )
            case PointsConfig.VoronoiConfig():
                raise NotImplementedError()

        # Include combat unit to help with expansion
        if config.use_combat_unit_positions == True:
            for _, _, transform in gs.query(CombatUnit, Transform):
                waypoints.append(transform.position)

        # Expands the points given the config
        for expansion_config in config.expansions:
            waypoints = AiPointsExpansionService._filter_colocated(waypoints)
            match expansion_config:
                case PointsConfig.LineBasedExpansionConfig():
                    waypoints = AiPointsExpansionService.expand_waypoints_line_based(
                        gs=gs,
                        initial_waypoints=waypoints,
                        tolerance=expansion_config.tolerance,
                    )
                case PointsConfig.PolygonalExpansionConfig():
                    raise NotImplementedError()
                case PointsConfig.FlagPruneConfig():
                    # Use combat unit positions as flags
                    flag_waypoints: list[Vec2] = []
                    if config.use_combat_unit_positions == True:
                        for _, _, transform in gs.query(CombatUnit, Transform):
                            flag_waypoints.append(transform.position)
                    waypoints = AiPointsExpansionService.prune_waypoints_by_flags(
                        gs=gs,
                        waypoints=waypoints,
                        flag_waypoints=flag_waypoints,
                    )
                case PointsConfig.WeightsPruneConfig():
                    # Use combat unit positions as flags
                    flag_waypoints: list[Vec2] = []
                    if config.use_combat_unit_positions == True:
                        for _, _, transform in gs.query(CombatUnit, Transform):
                            flag_waypoints.append(transform.position)
                    flagged_waypoints = AiPointsExpansionService._filter_colocated(
                        AiPointsExpansionService.prune_waypoints_by_flags(
                            gs=gs,
                            waypoints=waypoints,
                            flag_waypoints=flag_waypoints,
                        )
                    )
                    waypoints = AiPointsExpansionService.prune_waypoints_by_weight(
                        waypoints=waypoints,
                        remaining_size=expansion_config.remaining_size,
                        flagged_waypoints=flagged_waypoints,
                    )

        waypoints = AiPointsExpansionService._filter_colocated(waypoints)
        return waypoints

    @staticmethod
    def expand_waypoints_line_based(
        gs: GameState,
        initial_waypoints: list[Vec2],
        tolerance: float,
    ) -> list[Vec2]:
        """
        Given a list of waypoints, expand and create more waypoints
        representing move interrupt candidates.
        """
        los_system = gs.get(LosSystem)

        waypoints_los_polygon: dict[Vec2, list[Vec2]] = {}

        # FIXME: set does not guarantee co-location filter
        waypoints = set(initial_waypoints)

        terrain_vertices: list[list[Vec2]] = []
        for _, terrain, transform in gs.query(TerrainFeature, Transform):
            vertices = LinearTransform.apply(terrain.vertices, transform)
            if terrain.is_closed_loop:
                vertices.append(vertices[0])
            terrain_vertices.append(vertices)

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

                # Remove some intersects that are too closely packed
                unique_intersects: list[Vec2] = []
                for p in intersects:
                    if any(
                        (p - unique_p).length() <= tolerance
                        for unique_p in unique_intersects
                    ):
                        continue
                    unique_intersects.append(p)

                # Loop through each subsegment on this waypoint line pair
                # and add a new waypoint on the midpoint of subsegment.
                points_on_line: list[Vec2] = list(set(unique_intersects))
                points_on_line.append(waypoint_a)
                points_on_line.append(waypoint_b)
                points_on_line.sort(key=lambda p: (waypoint_a - p).length())
                for left_point, right_point in pairwise(points_on_line):
                    new_waypoints.add((left_point + right_point) / 2)

        # The 'or' operator |= is set concat
        waypoints |= new_waypoints
        return list(waypoints)

    @staticmethod
    def _get_flags(
        gs: GameState,
        waypoint: Vec2,
        flag_waypoints: list[Vec2],
    ) -> dict[Vec2, bool]:
        """
        Return visibility mapping of this waypoint against other flag waypoints.
        """
        los_system = gs.get(LosSystem)
        waypoint_los_polygon = los_system.get_los_polygon(gs, waypoint)
        return {
            other_waypoint: IntersectGetter.is_inside(
                other_waypoint, waypoint_los_polygon
            )
            for other_waypoint in flag_waypoints
        }

    @staticmethod
    def prune_waypoints_by_flags(
        gs: GameState,
        waypoints: list[Vec2],
        flag_waypoints: list[Vec2],
    ) -> list[Vec2]:
        """
        Removes waypoints that has duplicate flag values. The current flags
        used are intervisibility with other waypoints.
        """
        unique_waypoints: set[Vec2] = set()
        seen_flags: set[int] = set()
        for waypoint in waypoints:
            flags = AiPointsExpansionService._get_flags(gs, waypoint, flag_waypoints)
            # Flags are not hashable by default, so hash this in a dedicated step
            hashed_flags: int = hash(frozenset(flags.items()))
            if hashed_flags not in seen_flags:
                seen_flags.add(hashed_flags)
                unique_waypoints.add(waypoint)
        return list(unique_waypoints)

    @staticmethod
    def prune_waypoints_by_weight(
        waypoints: list[Vec2],
        remaining_size: int,
        flagged_waypoints: list[Vec2],
    ) -> list[Vec2]:
        """
        Removes waypoints with the lowest weight values. The weights
        currently used is the distance to nearest neighbour.
        """
        if remaining_size == 0:
            return []

        current_waypoints = list(waypoints)

        # Maintain a cache of weights and a lookup of nearest neighbor.
        # The nearest_to helps determine which cache to reset when pruned.
        waypoint_weights: dict[Vec2, float] = {}
        nearest_to: dict[Vec2, list[Vec2]] = {}

        def _get_weight(waypoint: Vec2, pool: list[Vec2]) -> float:
            if waypoint in waypoint_weights:  # Return from cache if exist
                return waypoint_weights[waypoint]

            # Cache miss, loop through pool to recalculate
            distance_to_each_waypoint = (
                ((other - waypoint).length(), other)
                for other in pool
                if other is not waypoint
            )
            min_dist, closest_neighbor = min(
                distance_to_each_waypoint,
                key=lambda i: i[0],
            )
            weight = min_dist
            if any(waypoint.is_close(flag) for flag in flagged_waypoints):
                weight += 1e10

            waypoint_weights[waypoint] = weight
            nearest_to.setdefault(closest_neighbor, []).append(waypoint)
            return weight

        # Keep removing the worst waypoint until we hit the target size
        while len(current_waypoints) > remaining_size:
            worst_waypoint = min(
                current_waypoints,
                key=lambda wp: _get_weight(wp, current_waypoints),
            )
            current_waypoints.remove(worst_waypoint)

            # Clear the cache of the affected waypoints
            waypoint_weights.pop(worst_waypoint)
            for affected in nearest_to.pop(worst_waypoint, []):
                waypoint_weights.pop(affected, None)

        return current_waypoints

    @staticmethod
    def _filter_colocated(
        waypoints: list[Vec2],
        tolerance: float = 1e-5,
    ) -> list[Vec2]:
        filtered_waypoints: list[Vec2] = []
        for waypoint in waypoints:
            if not any(
                waypoint.is_close(other, abs_tol=tolerance)
                for other in filtered_waypoints
            ):
                filtered_waypoints.append(waypoint)
        return filtered_waypoints
