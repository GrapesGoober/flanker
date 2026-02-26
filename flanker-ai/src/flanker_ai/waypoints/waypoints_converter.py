from dataclasses import replace
from typing import Literal

from flanker_ai.i_game_state_converter import IGameStateConverter
from flanker_ai.models import Action, AssaultAction, FireAction, MoveAction
from flanker_ai.waypoints.models import (
    WaypointAction,
    WaypointAssaultAction,
    WaypointFireAction,
    WaypointMoveAction,
)
from flanker_ai.waypoints.waypoints_game_state import (
    AbstractedCombatUnit,
    WaypointNode,
    WaypointsGameState,
)
from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    CombatUnit,
    EliminationObjective,
    FireControls,
    Transform,
)
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.los_system import LosSystem
from flanker_core.utils.intersect_getter import IntersectGetter


# TODO: this shouldn't be a separate class, but built into waypoint gs
class WaypointConverter(IGameStateConverter[WaypointAction, WaypointsGameState]):
    """
    Provides conversion logic between waypoints-graph and game state.
    This is done specifically for the CoG, thus the implementation here
    is aweful. The interconnections between nodes are too many.
    """

    def __init__(
        self,
        points: list[Vec2],
        path_tolerance: float,
    ) -> None:
        self._points = points
        self._path_tolerance = path_tolerance

    def deabstract_action(
        self,
        action: WaypointAction,
        representation: WaypointsGameState,
        gs: GameState,
    ) -> Action:
        match action:
            case WaypointMoveAction():
                return MoveAction(
                    unit_id=action.unit_id,
                    to=representation.waypoints[action.move_to_waypoint_id].position,
                )
            case WaypointFireAction():
                return FireAction(
                    unit_id=action.unit_id,
                    target_id=action.target_id,
                )
            case WaypointAssaultAction():
                return AssaultAction(
                    unit_id=action.unit_id,
                    target_id=action.target_id,
                )

    def create_template(
        self,
        gs: GameState,
    ) -> WaypointsGameState:
        """Create a waypoint-graph from the given list of points."""

        # Assemble waypoint-graph game state
        initiative = InitiativeSystem.get_initiative(gs)
        objectives: list[EliminationObjective] = list(
            [replace(objective) for _, objective in gs.query(EliminationObjective)]
        )
        waypoint_gs = WaypointsGameState(
            waypoints={},
            combat_units={},
            initiative=initiative,
            objectives=objectives,
        )

        # Add grid points as a waypoint
        for point_id, point in enumerate(self._points):
            waypoint_gs.waypoints[point_id] = WaypointNode(
                position=point,
                visible_nodes=set(),
                movable_paths={},
            )

        # Add relationships between nodes
        WaypointConverter._add_visibility_relationships(waypoint_gs, gs)
        WaypointConverter._add_path_relationships(
            waypoint_gs,
            path_tolerance=self._path_tolerance,
        )

        # Assemble the game state
        return waypoint_gs

    def update_template(
        self,
        gs: GameState,
        template: WaypointsGameState,
    ) -> WaypointsGameState:
        """Adds combat unit positions as waypoints."""

        new_waypoints = template.copy()
        new_waypoints.initiative = InitiativeSystem.get_initiative(gs)

        # Add combat units as waypoints and as abstracted units
        new_waypoint_ids: list[int] = []
        for unit_id, transform, combat_unit, fire_controls in gs.query(
            Transform, CombatUnit, FireControls
        ):
            waypoint_id = len(new_waypoints.waypoints.keys())
            new_waypoint_ids.append(waypoint_id)
            new_waypoints.waypoints[waypoint_id] = WaypointNode(
                position=transform.position,
                visible_nodes=set(),
                movable_paths={},
            )
            new_waypoints.combat_units[unit_id] = AbstractedCombatUnit(
                unit_id=unit_id,
                current_waypoint_id=waypoint_id,
                status=combat_unit.status,
                faction=combat_unit.faction,
                no_fire=not fire_controls.can_reactive_fire,
            )

        # Update their relationships
        WaypointConverter._add_path_relationships(
            waypoint_gs=new_waypoints,
            path_tolerance=self._path_tolerance,
            waypoint_ids_to_update=new_waypoint_ids,
        )
        WaypointConverter._add_visibility_relationships(
            waypoint_gs=new_waypoints,
            gs=gs,
            waypoint_ids_to_update=new_waypoint_ids,
        )

        # Update their objectives
        objectives: list[EliminationObjective] = list(
            [replace(objective) for _, objective in gs.query(EliminationObjective)]
        )
        new_waypoints.objectives = objectives

        return new_waypoints

    @staticmethod
    def _add_path_relationships(
        waypoint_gs: WaypointsGameState,
        path_tolerance: float,
        waypoint_ids_to_update: list[int] | Literal["all"] = "all",
    ) -> None:
        waypoints_to_update: list[tuple[int, WaypointNode]] = []
        if waypoint_ids_to_update == "all":
            waypoints_to_update = list(waypoint_gs.waypoints.items())
        else:
            waypoints_to_update = list(
                [(id, waypoint_gs.waypoints[id]) for id in waypoint_ids_to_update]
            )

        for waypoint_id, waypoint in waypoints_to_update:
            for move_id, move_waypoint in waypoint_gs.waypoints.items():
                move_from = waypoint.position
                move_to = move_waypoint.position
                move_distance = (move_to - move_from).length()
                direction = (move_to - move_from).normalized()

                # Define a set of nodes that forms the best path for this move
                path: list[tuple[int, float]] = []
                for path_id, path_waypoint in waypoint_gs.waypoints.items():
                    t = (path_waypoint.position - move_from).dot(direction)
                    if path_id in [waypoint_id, move_id]:
                        path.append((path_id, t))
                        continue
                    if t < 0:
                        continue
                    if t > move_distance:
                        continue
                    distance_to_line = (
                        (path_waypoint.position - move_from) - (direction * t)
                    ).length()
                    if distance_to_line > path_tolerance:
                        continue
                    path.append((path_id, t))

                def sort_key(node_entry: tuple[int, float]) -> float:
                    _, t = node_entry
                    return t

                waypoint.movable_paths[move_id] = list(
                    [id for id, _ in sorted(path, key=sort_key)]
                )

    @staticmethod
    def _add_visibility_relationships(
        waypoint_gs: WaypointsGameState,
        gs: GameState,
        waypoint_ids_to_update: list[int] | Literal["all"] = "all",
    ) -> None:
        waypoints_to_update: list[tuple[int, WaypointNode]] = []
        if waypoint_ids_to_update == "all":
            waypoints_to_update = list(waypoint_gs.waypoints.items())
        else:
            waypoints_to_update = list(
                [(id, waypoint_gs.waypoints[id]) for id in waypoint_ids_to_update]
            )

        # Compute LOS polygon for all these waypoints.
        # The LOS polygon might be overkill for now,
        # but future cases might need it
        waypoint_LOS_polygons: dict[int, list[Vec2]] = {}
        for waypoint_id, waypoint in waypoints_to_update:
            waypoint_LOS_polygons[waypoint_id] = LosSystem.get_los_polygon(
                gs, waypoint.position
            )

        # Add visibility relationships between nodes
        for waypoint_id, waypoint in waypoints_to_update:
            for other_id, other_waypoint in waypoint_gs.waypoints.items():
                # Add visibility relationship
                if IntersectGetter.is_inside(
                    other_waypoint.position, waypoint_LOS_polygons[waypoint_id]
                ):
                    waypoint.visible_nodes.add(other_id)
                    other_waypoint.visible_nodes.add(waypoint_id)
