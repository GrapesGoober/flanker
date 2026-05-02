from dataclasses import dataclass
from uuid import UUID

from flanker_core.models.vec2 import Vec2


@dataclass
class WaypointNode:
    position: Vec2
    visible_nodes: set[int]
    movable_paths: dict[int, list[int]]


@dataclass
class WaypointsGraphComponent:
    waypoints: dict[int, WaypointNode]


@dataclass
class UnitsWaypointsComponent:
    units_waypoint_ids: dict[UUID, int]
