from flanker_ai.config_models import PointsConfig
from flanker_core.gamestate import GameState
from flanker_core.models.components import CombatUnit, Transform
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.los_system import LosSystem
from flanker_core.utils.polygon_utils import PolygonUtils


class AiPointsFilterService:

    @staticmethod
    def filter_points(
        gs: GameState,
        config: PointsConfig,
        points: list[Vec2],
    ) -> list[Vec2]:
        for filter_config in config.filters:
            points = AiPointsFilterService._filter_colocated(points)
            match filter_config:
                case PointsConfig.LosSignaturesFilter():
                    # Use combat unit positions as flags
                    flag_waypoints: list[Vec2] = [
                        transform.position
                        for _, _, transform in gs.query(CombatUnit, Transform)
                    ]
                    points = AiPointsFilterService._filter_by_los(
                        gs=gs,
                        waypoints=points,
                        flag_waypoints=flag_waypoints,
                    )
                case _:
                    raise NotImplementedError()

        points = AiPointsFilterService._filter_colocated(points)
        return points

    @staticmethod
    def _filter_by_los(
        gs: GameState,
        waypoints: list[Vec2],
        flag_waypoints: list[Vec2],
    ) -> list[Vec2]:
        """
        Removes waypoints that has duplicate flag values. The current flags
        used are intervisibility with other waypoints.
        """

        def _get_los_flags(
            gs: GameState,
            waypoint: Vec2,
            flag_waypoints: list[Vec2],
        ) -> dict[Vec2, bool]:
            waypoint_los_polygon = LosSystem.get_los_polygon(gs, waypoint)
            return {
                other_waypoint: PolygonUtils.is_inside(
                    point=other_waypoint, polygon=waypoint_los_polygon
                )
                for other_waypoint in flag_waypoints
            }

        unique_waypoints: set[Vec2] = set()
        seen_flags: set[int] = set()
        for waypoint in waypoints:
            flags = _get_los_flags(gs, waypoint, flag_waypoints)
            # Flags are not hashable by default, so hash this in a dedicated step
            hashed_flags: int = hash(frozenset(flags.items()))
            if hashed_flags not in seen_flags:
                seen_flags.add(hashed_flags)
                unique_waypoints.add(waypoint)
        return list(unique_waypoints)

    @staticmethod
    def _filter_colocated(
        waypoints: list[Vec2],
        tolerance: float = 1e-5,
    ) -> list[Vec2]:
        filtered_waypoints: list[Vec2] = []
        for waypoint in waypoints:
            if not any(
                waypoint.is_close(other, abs_tol=tolerance)
                for other in filtered_waypoints
            ):
                filtered_waypoints.append(waypoint)
        return filtered_waypoints
