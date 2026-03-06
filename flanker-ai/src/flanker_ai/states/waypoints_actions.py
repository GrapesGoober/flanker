from dataclasses import dataclass


@dataclass
class WaypointMoveAction:
    unit_id: int
    move_to_waypoint_id: int
    interrupt_at_id: int | None


@dataclass
class WaypointFireAction:
    unit_id: int
    target_id: int


@dataclass
class WaypointAssaultAction:
    unit_id: int
    target_id: int
    interrupt_at_id: int | None


@dataclass
class WaypointPivotAction:
    unit_id: int
    degrees: float


WaypointAction = (
    WaypointMoveAction | WaypointFireAction | WaypointAssaultAction | WaypointPivotAction
)
