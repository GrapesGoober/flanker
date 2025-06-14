import math
from typing import List
from core.vec2 import Vec2


class TransformUtils:
    @staticmethod
    def offset(vec_list: List[Vec2], offset: Vec2) -> List[Vec2]:
        """Returns a new list of Vec2s, each one offset by the given Vec2."""
        return [vec + offset for vec in vec_list]

    @staticmethod
    def rotate(vec_list: List[Vec2], angle: float) -> List[Vec2]:
        """
        Rotates all Vec2s in the list around the origin by the given angle (in radians).
        """
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return [
            Vec2(x=(vec.x * cos_a - vec.y * sin_a), y=(vec.x * sin_a + vec.y * cos_a))
            for vec in vec_list
        ]
