from flanker_core.gamestate import GameState
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.los_system import LosSystem
from flanker_core.utils.intersect_getter import IntersectGetter


# TODO: move this into shared common
class WaypointsFlagService:
    @staticmethod
    def get_flags(
        gs: GameState,
        waypoint: Vec2,
        all_waypoints: set[Vec2],
    ) -> dict[Vec2, bool]:
        """Return visibility flags of this waypoint against all other waypoints."""
        los_system = gs.get(LosSystem)
        waypoint_los_polygon = los_system.get_los_polygon(gs, waypoint)
        return {
            other_waypoint: IntersectGetter.is_inside(
                other_waypoint, waypoint_los_polygon
            )
            for other_waypoint in all_waypoints
        }

    @staticmethod
    def prune_waypoints(
        gs: GameState,
        waypoints: set[Vec2],
    ) -> set[Vec2]:
        """Removes waypoints that has duplicate flag values."""
        unique_waypoints: set[Vec2] = set()
        seen_flags: set[int] = set()
        for waypoint in waypoints:
            flags = WaypointsFlagService.get_flags(gs, waypoint, waypoints)
            # Flags are not hashable by default, so hash this in a dedicated step
            hashed_flags: int = hash(frozenset(flags.items()))
            if hashed_flags not in seen_flags:
                seen_flags.add(hashed_flags)
                unique_waypoints.add(waypoint)
        return unique_waypoints

    @staticmethod
    def prune_waypoints_by_weight(
        waypoints: set[Vec2],
        remaining_size: int,
    ) -> set[Vec2]:
        """
        Returns a new set of waypoints where the lower weights are pruned.
        """

        def get_weight(waypoint: Vec2) -> float:
            distances = ((other - waypoint).length() for other in waypoints)
            return min(distances)

        sorted_waypoints = sorted(waypoints, key=get_weight, reverse=True)
        return set(sorted_waypoints[:remaining_size])
