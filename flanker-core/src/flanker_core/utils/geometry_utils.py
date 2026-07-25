from flanker_core.models.components import Transform
from flanker_core.models.vec2 import Vec2


class GeometryUtils:

    # TODO: just make a Vec2's "angle of"?
    # Use this "angle of" for both sorting and fov checks?
    @staticmethod
    def in_fov(
        origin_transform: Transform,
        target_pos: Vec2,
        fov: float = 90,
    ) -> bool:
        """
        Util method returns `True` if the position `target_pos`
        is in FOV cone of origin position `origin_transform`.
        """
        target_angle = origin_transform.position.angle_to(target_pos)

        # Wraps around to be in range [-180, 180]
        angle_diff = (target_angle - origin_transform.degrees + 180) % 360 - 180

        return abs(angle_diff) <= fov / 2
