from flanker_ai.waypoints.models import (
    WaypointActions,
    WaypointMoveAction,
    WaypointsGraphGameState,
)


class WaypointsMinimaxPlayer:
    """
    Implements a basic abstracted waypoints-graph minimax AI player.
    This is just a bare minimum code for the CoG paper, thus doesn't
    have RNG, determinism, or other fancier rigs.
    """

    @staticmethod
    def play(gs: WaypointsGraphGameState, depth: int) -> list[WaypointActions]: ...

    @staticmethod
    def _get_actions(gs: WaypointsGraphGameState) -> list[WaypointActions]:

        actions: list[WaypointActions] = []
        for combat_unit_id in gs.combat_units:
            combat_unit = gs.combat_units[combat_unit_id]
            current_waypoint = gs.waypoints[combat_unit.current_waypoint_id]
            for movable_neighbor_node_id in current_waypoint.movable_nodes:
                actions.append(
                    WaypointMoveAction(
                        unit_id=combat_unit_id,
                        move_to_waypoint_id=movable_neighbor_node_id,
                    )
                )

        return actions
