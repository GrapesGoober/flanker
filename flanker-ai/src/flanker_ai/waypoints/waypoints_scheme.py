from typing import Literal

from flanker_ai.unabstracted.models import (
    Action,
    ActionResult,
    AssaultAction,
    AssaultActionResult,
    FireAction,
    FireActionResult,
    MoveAction,
    MoveActionResult,
)
from flanker_ai.waypoints.models import (
    AbstractedCombatUnit,
    WaypointAction,
    WaypointAssaultAction,
    WaypointFireAction,
    WaypointMoveAction,
    WaypointNode,
    WaypointsGraphGameState,
)
from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    CombatUnit,
    FireControls,
    TerrainFeature,
    Transform,
)
from flanker_core.models.outcomes import InvalidAction
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.assault_system import AssaultSystem
from flanker_core.systems.fire_system import FireSystem
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.los_system import LosSystem
from flanker_core.systems.move_system import MoveSystem
from flanker_core.utils.intersect_getter import IntersectGetter
from flanker_core.utils.linear_transform import LinearTransform


class WaypointScheme:
    """
    Provides abstraction logic between waypoints-graph and game state.
    This is done specifically for the CoG, thus the implementation here
    is aweful. The interconnections between nodes are too many.
    """

    @staticmethod
    def deabstract_action(
        gs: WaypointsGraphGameState,
        action: WaypointAction,
    ) -> Action:
        match action:
            case WaypointMoveAction():
                return MoveAction(
                    unit_id=action.unit_id,
                    to=gs.waypoints[action.move_to_waypoint_id].position,
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

    @staticmethod
    def perform_action(
        gs: GameState,
        action: MoveAction | FireAction | AssaultAction,
    ) -> ActionResult | InvalidAction:
        match action:
            case MoveAction():
                result = MoveSystem.move(gs, action.unit_id, action.to)
                if not isinstance(result, InvalidAction):
                    return MoveActionResult(
                        action=action,
                        result_gs=gs,
                        reactive_fire_outcome=result.reactive_fire_outcome,
                    )
            case FireAction():
                result = FireSystem.fire(gs, action.unit_id, action.target_id)
                if not isinstance(result, InvalidAction):
                    return FireActionResult(
                        action=action,
                        result_gs=gs,
                        outcome=result.outcome,
                    )
            case AssaultAction():
                result = AssaultSystem.assault(gs, action.unit_id, action.target_id)
                if not isinstance(result, InvalidAction):
                    return AssaultActionResult(
                        action=action,
                        result_gs=gs,
                        outcome=result.outcome,
                        reactive_fire_outcome=result.reactive_fire_outcome,
                    )
        return result

    @staticmethod
    def apply_action(
        gs: GameState,
        waypoint_gs: WaypointsGraphGameState,
        waypoint_action: WaypointAction,
    ) -> ActionResult | InvalidAction:
        action = WaypointScheme.deabstract_action(waypoint_gs, waypoint_action)
        result = WaypointScheme.perform_action(gs, action)
        return result

    @staticmethod
    def create_grid_waypoints(
        gs: GameState,
        spacing: float,
        offset: float,
    ) -> WaypointsGraphGameState:

        # Assemble waypoint-graph game state
        initiative = InitiativeSystem.get_initiative(gs)
        waypoint_gs = WaypointsGraphGameState(
            waypoints={},
            combat_units={},
            initiative=initiative,
        )

        # Add grid points as a waypoint
        points = WaypointScheme._get_grid_coordinates(gs, spacing, offset)
        for point_id, point in enumerate(points):
            waypoint_gs.waypoints[point_id] = WaypointNode(
                position=point,
                visible_nodes=set(),
                movable_paths={},
            )

        # Add relationships between nodes
        WaypointScheme._add_visibility_relationships(waypoint_gs, gs)
        WaypointScheme._add_path_relationships(
            waypoint_gs,
            path_tolerance=spacing * 0.5,
        )

        # Assemble the game state
        return waypoint_gs

    @staticmethod
    def add_combat_units(
        waypoint_gs: WaypointsGraphGameState,
        gs: GameState,
        path_tolerance: float,
    ) -> None:

        # Add combat units as waypoints and as abstracted units
        new_waypoint_ids: list[int] = []
        for unit_id, transform, combat_unit, fire_controls in gs.query(
            Transform, CombatUnit, FireControls
        ):
            waypoint_id = len(waypoint_gs.waypoints.keys())
            new_waypoint_ids.append(waypoint_id)
            waypoint_gs.waypoints[waypoint_id] = WaypointNode(
                position=transform.position,
                visible_nodes=set(),
                movable_paths={},
            )
            waypoint_gs.combat_units[unit_id] = AbstractedCombatUnit(
                unit_id=unit_id,
                current_waypoint_id=waypoint_id,
                status=combat_unit.status,
                faction=combat_unit.faction,
                no_fire=not fire_controls.can_reactive_fire,
            )

        # Update their relationships
        WaypointScheme._add_path_relationships(
            waypoint_gs=waypoint_gs,
            path_tolerance=path_tolerance,
            waypoint_ids_to_update=new_waypoint_ids,
        )
        WaypointScheme._add_visibility_relationships(
            waypoint_gs=waypoint_gs,
            gs=gs,
            waypoint_ids_to_update=new_waypoint_ids,
        )

    @staticmethod
    def _get_grid_coordinates(
        gs: GameState,
        spacing: float,
        offset: float,
    ) -> list[Vec2]:

        # Build an array of grids within the boundary
        mask = TerrainFeature.Flag.BOUNDARY
        boundary_vertices: list[Vec2] | None = None
        for _, terrain, transform in gs.query(TerrainFeature, Transform):
            if terrain.flag & mask:
                boundary_vertices = LinearTransform.apply(
                    terrain.vertices,
                    transform,
                )
                if terrain.is_closed_loop:
                    boundary_vertices.append(boundary_vertices[0])

        assert boundary_vertices, "Can't abstract; boundary terrain missing!"

        # Boundary terrrain might not be a box
        min_x = min(v.x for v in boundary_vertices) + offset
        max_x = max(v.x for v in boundary_vertices)
        min_y = min(v.y for v in boundary_vertices) + offset
        max_y = max(v.y for v in boundary_vertices)

        # Generates waypoints at specified spacing
        points: list[Vec2] = []
        y = min_y
        while y <= max_y:
            x = min_x
            while x <= max_x:
                p = Vec2(x, y)

                # Keep only points inside polygon
                if IntersectGetter.is_inside(p, boundary_vertices):
                    points.append(p)

                x += spacing
            y += spacing
        return points

    @staticmethod
    def _add_path_relationships(
        waypoint_gs: WaypointsGraphGameState,
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
            if waypoint_id % 10 == 0:
                progress = waypoint_id / len(waypoint_gs.waypoints)
                print(f"abstracting {progress * 100:.2f}%")
            for move_id, move_waypoint in waypoint_gs.waypoints.items():
                move_from = waypoint.position
                move_to = move_waypoint.position
                move_distance = (move_to - move_from).length()
                direction = (move_to - move_from).normalized()

                # Define a set of nodes that forms the best path for this move
                path: list[tuple[int, float]] = []
                for path_id, path_waypoint in waypoint_gs.waypoints.items():
                    t = (path_waypoint.position - move_from).dot(direction)
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
        waypoint_gs: WaypointsGraphGameState,
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
