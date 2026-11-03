from uuid import UUID

from flanker_core.gamestate import GameState
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.los_system import LosSystem


class AiAspectSignatureService:

    @staticmethod
    def _get_angle_bounds(
        position: Vec2,
        vertices: list[Vec2],
    ) -> tuple[float, float]:
        # TODO: this code is AI generated. Although it is probably correct,
        # this is such a mess that I don't wanna use it.
        # I should clean this up. I should handle this edge case myself.
        angles = sorted(position.angle_to(vertex) % 360.0 for vertex in vertices)
        angles.append(angles[0] + 360.0)

        # The obstacle is the arc opposite the largest gap between vertices.
        gap_start, gap_end = max(
            zip(angles, angles[1:]),
            key=lambda pair: pair[1] - pair[0],
        )

        left = gap_end % 360.0
        right = gap_start
        if right < left:
            right += 360.0

        # Keep the left bound in angle_to's [-180, 180] range.
        if left > 180.0:
            left -= 360.0
            right -= 360.0

        return left, right

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
        return aspect_angles
