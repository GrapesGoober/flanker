from typing import override

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
