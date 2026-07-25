import math

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

        # Direction the spotter is facing
        heading_rad = math.radians(origin_transform.degrees)
        forward_dir: Vec2 = Vec2(1, 0).rotated(heading_rad)

        # Direction to target
        to_target = (target_pos - origin_transform.position).normalized()

        # Dot product -> angle check
        dot = forward_dir.dot(to_target)

        # cos(theta) comparison (avoid expensive acos)
        half_fov_rad = math.radians(fov / 2)
        return dot >= math.cos(half_fov_rad)
