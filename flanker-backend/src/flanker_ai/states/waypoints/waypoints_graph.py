from dataclasses import dataclass

from flanker_core.gamestate import GameState
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.los_system import LosSystem
from flanker_core.utils.polygon_utils import PolygonUtils


@dataclass
class WaypointNode:
    position: Vec2
    visible_nodes: set[int]
    movable_paths: dict[int, list[int]]


@dataclass
class _WaypointsGraphComponent:
    waypoint_positions: dict[tuple[int, int], int]
    waypoints: dict[int, WaypointNode]


class WaypointsGraph:
    """
    Defines operations for waypoints-graph initialization, getters,
    pathing, and visibility logic. This is meant for waypoints-graph state.
    """

    @staticmethod
    def _get_waypoints_graph(
        gs: GameState,
    ) -> _WaypointsGraphComponent:
        if entities := gs.query(_WaypointsGraphComponent):
            _, graph_component = entities[0]
            return graph_component
        else:
            raise ValueError("Waypoints not configured in this game state.")

    @staticmethod
    def get_waypoints(
        gs: GameState,
    ) -> dict[int, WaypointNode]:
        """Get a configured waypoints dictionary"""
        return WaypointsGraph._get_waypoints_graph(gs).waypoints

    @staticmethod
    def get_waypoint_id(
        gs: GameState,
        position: Vec2,
    ) -> int:
        """Returns a waypoint ID from coerced position."""
        graph = WaypointsGraph._get_waypoints_graph(gs)

        # Use the waypoint lookup table if the position exists
        rounded_position = (int(position.x), int(position.y))
        if rounded_position in graph.waypoint_positions:
            return graph.waypoint_positions[rounded_position]

        # If position doesn't exist, use expensive linear search
        coerced_waypoint_id = min(
            graph.waypoints.keys(),
            key=lambda idx: (position - graph.waypoints[idx].position).length(),
        )
        return coerced_waypoint_id

    @staticmethod
    def get_waypoint(
        gs: GameState,
        position: Vec2,
    ) -> WaypointNode:
        """Returns a waypoint object from coerced position."""
        waypoint_id = WaypointsGraph.get_waypoint_id(gs, position)
        waypoints = WaypointsGraph.get_waypoints(gs)
        return waypoints[waypoint_id]

    @staticmethod
    def set_waypoints(
        gs: GameState,
        points: list[Vec2],
        path_tolerance: float,
    ) -> None:
        """Sets a new waypoints graph configured on the given waypoints"""
        # Creates or resets a new empty singleton graph if not exists.
        if entities := gs.query(_WaypointsGraphComponent):
            _, component = entities[0]
        else:
            gs.add_entity(component := _WaypointsGraphComponent({}, {}))
        waypoints = component.waypoints
        waypoints.clear()

        # Add new empty waypoints placed on specific coordinates
        for point_id, point in enumerate(points):
            waypoints[point_id] = WaypointNode(
                position=point,
                visible_nodes=set(),
                movable_paths={},
            )

        # Create a lookup table for waypoint positions
        component.waypoint_positions = {
            (
                int(waypoint.position.x),
                int(waypoint.position.y),
            ): waypoint_id
            for waypoint_id, waypoint in waypoints.items()
        }

        # Add relationships between nodes
        WaypointsGraph._add_visibility_relationships(gs)
        WaypointsGraph._add_path_relationships(gs, path_tolerance)

    @staticmethod
    def _add_path_relationships(
        gs: GameState,
        path_tolerance: float,
    ) -> None:
        waypoints = WaypointsGraph.get_waypoints(gs)

        # Create neighboring relationships for each waypoint
        waypoint_neighbors: dict[int, list[int]] = {}
        for waypoint_id, waypoint in waypoints.items():
            waypoint_neighbors[waypoint_id] = [
                neighbor_id
                for neighbor_id, neighbor_waypoint in waypoints.items()
                if (neighbor_waypoint.position - waypoint.position).length()
                < path_tolerance
            ]

        # For each waypoint pair, find an approximate waypoints path
        # Just greedily search for speed
        for waypoint_id, waypoint in waypoints.items():
            for move_id, move_waypoint in waypoints.items():
                path: list[int] = [waypoint_id]
                current_id = waypoint_id
                visited: set[int] = {current_id}

                while current_id != move_id:
                    neighbors = [
                        neighbor_id
                        for neighbor_id in waypoint_neighbors[current_id]
                        if neighbor_id not in visited
                    ]
                    if neighbors == []:
                        break

                    current_id = min(
                        neighbors,
                        key=lambda neighbor_id: (
                            waypoints[neighbor_id].position - move_waypoint.position
                        ).length(),
                    )
                    visited.add(current_id)
                    path.append(current_id)

                if current_id == move_id:
                    waypoint.movable_paths[move_id] = path

    @staticmethod
    def _add_visibility_relationships(
        gs: GameState,
    ) -> None:
        # Compute LOS polygon for all these waypoints.
        # The LOS polygon might be overkill for now,
        # but future cases might need it
        waypoints = WaypointsGraph.get_waypoints(gs)
        waypoint_LOS_polygons: dict[int, list[Vec2]] = {}
        for waypoint_id, waypoint in waypoints.items():
            waypoint_LOS_polygons[waypoint_id] = LosSystem.get_los_polygon(
                gs, waypoint.position
            )

        # Add visibility relationships between nodes
        for waypoint_id, waypoint in waypoints.items():
            for other_id, other_waypoint in waypoints.items():
                # Add visibility relationship
                if PolygonUtils.is_inside(
                    other_waypoint.position, waypoint_LOS_polygons[waypoint_id]
                ):
                    waypoint.visible_nodes.add(other_id)
                    other_waypoint.visible_nodes.add(waypoint_id)
