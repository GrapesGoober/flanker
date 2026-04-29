from typing import override
from uuid import UUID

from flanker_ai.states.waypoints.models import WaypointsGraphComponent
from flanker_core.gamestate import GameState
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
        # This uses precomputed pathing to get the earliest
        # point along the path that has valid LOS.
        ...
