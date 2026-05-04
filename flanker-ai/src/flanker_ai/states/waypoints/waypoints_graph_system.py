from flanker_ai.states.waypoints.models import WaypointNode, WaypointsGraphComponent
from flanker_core.gamestate import GameState
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.los_system import LosSystem
from flanker_core.utils.intersect_getter import IntersectGetter


class WaypointGraphSystem:
    @staticmethod
    def get_waypoints(gs: GameState) -> dict[int, WaypointNode]:
        if entities := gs.query(WaypointsGraphComponent):
            _, component = entities[0]
        else:
            gs.add_entity(component := WaypointsGraphComponent({}))
        return component.waypoints

    @staticmethod
    def get_waypoint_id(gs: GameState, position: Vec2) -> int:
        waypoints_system = gs.get(WaypointGraphSystem)
        waypoints = waypoints_system.get_waypoints(gs)
        coerced_waypoint_id = min(
            waypoints.keys(),
            key=lambda idx: abs((position - waypoints[idx].position).length()),
        )
        return coerced_waypoint_id

    @staticmethod
    def set_waypoints(gs: GameState, points: list[Vec2], path_tolerance: float) -> None:
        waypoints_system = gs.get(WaypointGraphSystem)
        waypoints = waypoints_system.get_waypoints(gs)
        waypoints.clear()

        # Add new empty waypoints placed on specific coordinates
        for point_id, point in enumerate(points):
            waypoints[point_id] = WaypointNode(
                position=point,
                visible_nodes=set(),
                movable_paths={},
            )

        # Add relationships between nodes
        waypoints_system._add_visibility_relationships(gs)
        waypoints_system._add_path_relationships(gs, path_tolerance)

    @staticmethod
    def _add_path_relationships(
        gs: GameState,
        path_tolerance: float,
    ) -> None:
        waypoints_system = gs.get(WaypointGraphSystem)

        waypoints = waypoints_system.get_waypoints(gs)
        for waypoint_id, waypoint in waypoints.items():
            for move_id, move_waypoint in waypoints.items():
                move_from = waypoint.position
                move_to = move_waypoint.position
                move_distance = (move_to - move_from).length()
                direction = (move_to - move_from).normalized()

                # Define a set of nodes that forms the best path for this move
                path: list[tuple[int, float]] = []
                for path_id, path_waypoint in waypoints.items():
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
        gs: GameState,
    ) -> None:

        waypoints_system = gs.get(WaypointGraphSystem)
        los_system = gs.get(LosSystem)

        # Compute LOS polygon for all these waypoints.
        # The LOS polygon might be overkill for now,
        # but future cases might need it
        waypoints = waypoints_system.get_waypoints(gs)
        waypoint_LOS_polygons: dict[int, list[Vec2]] = {}
        for waypoint_id, waypoint in waypoints.items():
            waypoint_LOS_polygons[waypoint_id] = los_system.get_los_polygon(
                gs, waypoint.position
            )

        # Add visibility relationships between nodes
        for waypoint_id, waypoint in waypoints.items():
            for other_id, other_waypoint in waypoints.items():
                # Add visibility relationship
                if IntersectGetter.is_inside(
                    other_waypoint.position, waypoint_LOS_polygons[waypoint_id]
                ):
                    waypoint.visible_nodes.add(other_id)
                    other_waypoint.visible_nodes.add(waypoint_id)
