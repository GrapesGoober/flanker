from uuid import UUID

from flanker_ai.states.waypoints.waypoints_graph_system import WaypointsGraphSystem
from flanker_core.gamestate import GameState
from flanker_core.models.components import Transform
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.los_system import LosSystem


class WaypointsLosSystemOverrides:

    @staticmethod
    def has_los(
        gs: GameState,
        spotter_pos: Vec2,
        target_pos: Vec2,
    ) -> bool:
        """
        Override using precomputed waypoint visibility.
        """

        waypoints_system = gs.get(WaypointsGraphSystem)
        spotter_waypoint = waypoints_system.get_waypoint(gs, spotter_pos)
        target_waypoint_id = waypoints_system.get_waypoint_id(gs, target_pos)
        return target_waypoint_id in spotter_waypoint.visible_nodes

    @staticmethod
    def get_los_from_line(
        gs: GameState,
        spotter_id: UUID,
        line: tuple[Vec2, Vec2],
    ) -> Vec2 | None:
        """
        Override using cheaper waypoint-based move interrupt.
        This returns the earliest waypoint along the move path that
        has a valid LOS to the spotter.
        """

        waypoints_system = gs.get(WaypointsGraphSystem)

        # Coerce the positions to waypoints
        start_waypoint = waypoints_system.get_waypoint(gs, line[0])
        end_waypoint_id = waypoints_system.get_waypoint_id(gs, line[1])
        spotter_transform = gs.get_component(spotter_id, Transform)
        spotter_waypoint_id = waypoints_system.get_waypoint_id(
            gs, spotter_transform.position
        )

        # Loop through each path nodes to find the earliest valid LOS waypoint
        waypoints = waypoints_system.get_waypoints(gs)
        path_waypoint_ids = start_waypoint.movable_paths[end_waypoint_id]
        for path_id in path_waypoint_ids:
            path_waypoint = waypoints[path_id]
            if spotter_waypoint_id not in path_waypoint.visible_nodes:
                continue
            if not LosSystem.in_fov(spotter_transform, path_waypoint.position):
                continue
            return path_waypoint.position

        return None
