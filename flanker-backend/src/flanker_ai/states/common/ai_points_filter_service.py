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
                case PointsConfig.IngressLosSignaturesFilter():
                    # returns both LOS filtered waypoints and ingress waypoints
                    flag_waypoints: list[Vec2] = [
                        transform.position
                        for _, _, transform in gs.query(CombatUnit, Transform)
                    ]
                    los_filtered = AiPointsFilterService._filter_by_los(
                        gs=gs,
                        waypoints=points,
                        flag_waypoints=flag_waypoints,
                    )
                    ingress_filtered = AiPointsFilterService._filter_by_ingress(
                        gs=gs,
                        waypoints=points,
                        target_waypoints=los_filtered,
                        ingress_fov=90,
                    )
                    points = ingress_filtered + los_filtered

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
        used are LOS intervisibility with other waypoints.
        """

        unique_waypoints: list[Vec2] = []
        seen_flags: set[int] = set()
        for waypoint in waypoints:
            waypoint_los_polygon = LosSystem.get_los_polygon(gs, waypoint)
            flags = {
                other_waypoint: PolygonUtils.is_inside(
                    point=other_waypoint, polygon=waypoint_los_polygon
                )
                for other_waypoint in flag_waypoints
            }
            # Flags are not hashable by default, so hash this in a dedicated step
            hashed_flags: int = hash(frozenset(flags.items()))
            if hashed_flags not in seen_flags:
                seen_flags.add(hashed_flags)
                unique_waypoints.append(waypoint)
        return unique_waypoints

    @staticmethod
    def _filter_by_ingress(
        gs: GameState,
        waypoints: list[Vec2],
        target_waypoints: list[Vec2],
        ingress_fov: float,
    ) -> list[Vec2]:
        """Get a list of distinct ingress nodes that satisfies target waypoints."""

        ingress_waypoints: list[Vec2] = []
        seen_signatures: set[tuple[bool, ...]] = set()
        for ingress_candidate in waypoints:
            for target_waypoint in target_waypoints:
                ingress_angle = ingress_candidate.angle_to(target_waypoint)
                target_los_polygon = LosSystem.get_los_polygon(gs, target_waypoint)
                fov_clipped_los = PolygonUtils.clip_by_fov_cone(
                    polyline=target_los_polygon,
                    center_point=target_waypoint,
                    heading_degree=ingress_angle,
                    fov_degree=ingress_fov,
                )
                signature: tuple[bool, ...] = tuple(
                    [
                        PolygonUtils.is_inside(transform.position, fov_clipped_los)
                        for _, _, transform in gs.query(CombatUnit, Transform)
                    ]
                )
                if signature not in seen_signatures:
                    ingress_waypoints.append(ingress_candidate)
                    seen_signatures.add(signature)

        return ingress_waypoints

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
