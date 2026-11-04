from uuid import UUID

from flanker_core.gamestate import GameState
from flanker_core.models.components import CombatUnit, Transform
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.los_system import LosSystem


class AiAspectSignatureService:

    @staticmethod
    def _get_angle_bounds(
        position: Vec2,
        vertices: list[Vec2],
    ) -> tuple[float, float]:
        left_vector = vertices[0] - position
        right_vector = vertices[0] - position

        for vertex in vertices:
            current_vector = vertex - position

            cross_product = left_vector.cross(current_vector)
            if cross_product > 0:
                left_vector = current_vector

            cross_product = right_vector.cross(current_vector)
            if cross_product < 0:
                right_vector = current_vector

        left_angle = position.angle_to(position + left_vector)
        right_angle = position.angle_to(position + right_vector)
        return left_angle, right_angle

    @staticmethod
    def get_aspects_angles(
        gs: GameState,
        position: Vec2,
    ) -> list[tuple[UUID, float]]:
        """
        Given a position, generates a list of aspects angles between this point
        towards obstacles.
        """

        obstacles = LosSystem.get_obstacles(gs, position)
        aspect_angles: list[tuple[UUID, float]] = []
        for obstacle in obstacles:
            if len(obstacle.polyline) != 0:
                left_bound, right_bound = AiAspectSignatureService._get_angle_bounds(
                    position, obstacle.polyline
                )
                aspect_angles.append((obstacle.metadata, left_bound))
                aspect_angles.append((obstacle.metadata, right_bound))

        # Add combat unit aspect signatures
        for other_unit_id, _, other_transform in gs.query(CombatUnit, Transform):
            if other_transform.position.is_close(position):
                continue
            angle = position.angle_to(other_transform.position)
            aspect_angles.append((other_unit_id, angle))

        return aspect_angles
