from dataclasses import dataclass

from flanker_core.models.components import (
    CombatUnit,
    EliminationObjective,
    InitiativeState,
)
from flanker_core.models.vec2 import Vec2


@dataclass
class AbstractedCombatUnit:
    # Note: this should be kept flat to be serializable
    unit_id: int
    current_waypoint_id: int
    status: CombatUnit.Status
    faction: InitiativeState.Faction
    no_fire: bool


@dataclass
class WaypointNode:
    position: Vec2
    visible_nodes: set[int]
    movable_paths: dict[int, list[int]]


@dataclass
class WaypointsGraphGameState:  # Used as state representation
    # Note: this should be kept flat to be serializable in the future
    waypoints: dict[int, WaypointNode]
    combat_units: dict[int, AbstractedCombatUnit]
    initiative: InitiativeState.Faction
    objectives: list[EliminationObjective]


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


WaypointAction = WaypointMoveAction | WaypointFireAction | WaypointAssaultAction
