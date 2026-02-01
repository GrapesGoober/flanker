from dataclasses import dataclass

from flanker_core.gamestate import GameState
from flanker_core.models.components import CombatUnit, InitiativeState
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
    visible_nodes: list[int]
    movable_nodes: list[int]


@dataclass
class WaypointsGraphGameState:  # Used for the minimax
    # Note: this should be kept flat to be serializable
    game_state: GameState
    waypoints: dict[int, WaypointNode]
    combat_units: dict[int, AbstractedCombatUnit]


@dataclass
class WaypointMoveAction:
    unit_id: int
    move_to_waypoint_id: int


@dataclass
class WaypointFireAction:
    unit_id: int
    target_id: int


@dataclass
class WaypointAssaultAction:
    unit_id: int
    target_id: int


WaypointActions = WaypointMoveAction | WaypointFireAction | WaypointAssaultAction
