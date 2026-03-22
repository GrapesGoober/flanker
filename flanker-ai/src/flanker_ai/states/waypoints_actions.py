from dataclasses import dataclass
from uuid import UUID


@dataclass
class WaypointMoveAction:
    unit_id: UUID
    move_to_waypoint_id: int


@dataclass
class WaypointPivotAction:
    unit_id: UUID
    pivot_to_waypoint_id: int


@dataclass
class WaypointFireAction:
    unit_id: UUID
    target_id: UUID


@dataclass
class WaypointAssaultAction:
    unit_id: UUID
    target_id: UUID


WaypointAction = (
    WaypointMoveAction
    | WaypointFireAction
    | WaypointAssaultAction
    | WaypointPivotAction
)
