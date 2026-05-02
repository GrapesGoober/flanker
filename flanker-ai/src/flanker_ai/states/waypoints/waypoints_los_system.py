from typing import override
from uuid import UUID

from flanker_ai.states.waypoints.models import WaypointsGraphComponent
from flanker_core.gamestate import GameState
from flanker_core.models.components import Transform
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.los_system import LosSystem


class WaypointsLosSystem(LosSystem):

    @staticmethod
    @override
    def has_los(gs: GameState, spotter_pos: Vec2, target_pos: Vec2) -> bool:

        _, waypoints_component = gs.query(WaypointsGraphComponent)[0]
        waypoints = waypoints_component.waypoints

        spotter_waypoint = min(
            waypoints.values(),
            key=lambda waypoint: abs((spotter_pos - waypoint.position).length()),
        )
        target_waypoint_id = min(
            waypoints.keys(),
            key=lambda idx: abs((target_pos - waypoints[idx].position).length()),
        )

        return target_waypoint_id in spotter_waypoint.visible_nodes

    @staticmethod
    @override
    def get_los_from_line(
        gs: GameState,
        spotter_id: UUID,
        line: tuple[Vec2, Vec2],
    ) -> Vec2 | None:
        # This override is intended for the move interrupt logic.
        # This returns the earliest waypoint along the move path that
        # has a valid LOS to the spotter

        los_system = gs.get(LosSystem)
        _, waypoints_component = gs.query(WaypointsGraphComponent)[0]
        waypoints = waypoints_component.waypoints

        # Coerce the positions to waypoints
        start_waypoint = min(
            waypoints.values(),
            key=lambda waypoint: abs((line[0] - waypoint.position).length()),
        )
        end_waypoint_id = min(
            waypoints.keys(),
            key=lambda idx: abs((line[1] - waypoints[idx].position).length()),
        )
        spotter_transform = gs.get_component(spotter_id, Transform)
        spotter_waypoint_id = min(
            waypoints.keys(),
            key=lambda idx: abs(
                (spotter_transform.position - waypoints[idx].position).length(),
            ),
        )

        # Loop through each path nodes to find the earliest valid LOS waypoint
        path_waypoint_ids = start_waypoint.movable_paths[end_waypoint_id]
        for path_id in path_waypoint_ids:
            path_waypoint = waypoints[path_id]
            if spotter_waypoint_id not in path_waypoint.visible_nodes:
                continue
            if not los_system.in_fov(spotter_transform, path_waypoint.position):
                continue
            return path_waypoint.position

        return None
