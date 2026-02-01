from flanker_ai.unabstracted.models import ActionResult, MoveAction, MoveActionResult
from flanker_ai.waypoints.models import (
    AbstractedCombatUnit,
    WaypointActions,
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
    InitiativeState,
    TerrainFeature,
    Transform,
)
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.los_system import LosSystem
from flanker_core.utils.intersect_getter import IntersectGetter
from flanker_core.utils.linear_transform import LinearTransform


class WaypointScheme:
    """
    Provides abstraction logic between waypoints-graph and game state.
    This is done specifically for the CoG, thus the implementation here
    is aweful. The interconnections between nodes are too many.
    """

    @staticmethod
    def create_grid_waypoints(
        gs: GameState,
        spacing: float,
        offset: float,
    ) -> WaypointsGraphGameState:

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

        assert boundary_vertices

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

        # Assemble waypoint-graph game state
        if results := gs.query(InitiativeState):
            _, initiative_state = results[0]
        else:
            raise ValueError(f"Component {InitiativeState} doesn't exist")
        initiative = initiative_state.faction
        waypoint_gs = WaypointsGraphGameState(
            game_state=gs,
            waypoints={},
            combat_units={},
            initiative=initiative,
        )

        # Add grid points as a waypoint
        for point_id, point in enumerate(points):
            waypoint_gs.waypoints[point_id] = WaypointNode(
                position=point, visible_nodes=[], movable_nodes=[]
            )

        # Add combat units as waypoints and as abstracted units
        for unit_id, transform, combat_unit, fire_controls in gs.query(
            Transform, CombatUnit, FireControls
        ):
            waypoint_id = len(waypoint_gs.waypoints.keys())
            waypoint_gs.waypoints[waypoint_id] = WaypointNode(
                position=transform.position,
                visible_nodes=[],
                movable_nodes=[],
            )
            waypoint_gs.combat_units[unit_id] = AbstractedCombatUnit(
                unit_id=unit_id,
                current_waypoint_id=waypoint_id,
                status=combat_unit.status,
                faction=combat_unit.faction,
                no_fire=not fire_controls.can_reactive_fire,
            )

        # Compute LOS polygon for all these waypoints
        waypoint_LOS_polygons: dict[int, list[Vec2]] = {}
        for waypoint_id, waypoint in waypoint_gs.waypoints.items():
            waypoint_LOS_polygons[waypoint_id] = LosSystem.get_los_polygon(
                gs, waypoint.position
            )

        # Add relationships between nodes
        # Max distance cap to prevent complete graph
        MOVABLE_DISTANCE = 21
        for waypoint_id, waypoint in waypoint_gs.waypoints.items():
            for other_id, other_waypoint in waypoint_gs.waypoints.items():
                distance = (waypoint.position - other_waypoint.position).length()
                # Add movable relationship
                # TODO: add move interrupts
                # FIXME: have it only append RELEVANT nodes, not just distance
                # Otherwise there's too high branching factor while
                if distance < MOVABLE_DISTANCE:
                    waypoint.movable_nodes.append(other_id)

                # Add visibility relationship
                if IntersectGetter.is_inside(
                    other_waypoint.position, waypoint_LOS_polygons[waypoint_id]
                ):
                    waypoint.visible_nodes.append(other_id)

        # Assemble the game state
        return waypoint_gs

    @staticmethod
    def deabstract_actions(
        gs: WaypointsGraphGameState,
        actions: list[WaypointActions],
    ) -> list[ActionResult]:
        results: list[ActionResult] = []
        for action in actions:
            match action:
                case WaypointMoveAction():
                    results.append(
                        MoveActionResult(
                            action=MoveAction(
                                unit_id=action.unit_id,
                                to=gs.waypoints[action.move_to_waypoint_id].position,
                            ),
                            result_gs=GameState(),
                            reactive_fire_outcome=None,
                        )
                    )
                    ...
                case WaypointFireAction():
                    ...
                case WaypointAssaultAction():
                    ...
        return results
