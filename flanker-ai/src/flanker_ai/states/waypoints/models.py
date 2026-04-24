from dataclasses import dataclass, field

from flanker_core.models.vec2 import Vec2


@dataclass
class WaypointNode:
    position: Vec2
    visible_nodes: set[int]
    movable_paths: dict[int, list[int]]


@dataclass
class WaypointsGraphComponent:
    waypoints: dict[int, WaypointNode] = field(
        default_factory=dict[int, WaypointNode],
    )
