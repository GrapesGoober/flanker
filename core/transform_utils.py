import math
from typing import List
from core.components import Transform
from core.vec2 import Vec2


class TransformUtils:
    """Utils for coordinate transformations via `Transform` component."""

    @staticmethod
    def translate(vec_list: List[Vec2], offset: Vec2) -> List[Vec2]:
        """Returns a new `list[Vec2]` translated by an `offset`."""
        return [vec + offset for vec in vec_list]

    @staticmethod
    def rotate(vec_list: List[Vec2], angle: float) -> List[Vec2]:
        """Returns a new `list[Vec2]` rotated by `angle` (in radians)."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return [
            Vec2(x=(vec.x * cos_a - vec.y * sin_a), y=(vec.x * sin_a + vec.y * cos_a))
            for vec in vec_list
        ]

    @staticmethod
    def apply(vec_list: List[Vec2], transform: Transform) -> list[Vec2]:
        """Returns a new `list[Vec2` translated and rotated by `Transform`."""
        rotated = TransformUtils.rotate(vec_list, transform.angle)
        translated = TransformUtils.translate(rotated, transform.position)
        return translated
