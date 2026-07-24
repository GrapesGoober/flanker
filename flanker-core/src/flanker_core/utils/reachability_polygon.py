from dataclasses import dataclass
from typing import Callable

from flanker_core.models.vec2 import Vec2


@dataclass
class Obstacle[T]:
    vertices: list[Vec2]
    metadata: T


@dataclass
class Intersection[T]:
    obstacle: Obstacle[T]
    point: Vec2


class ReachabilityPolygon:
    @staticmethod
    def get_polygon[T](
        point: Vec2,
        obstacles: list[Obstacle[T]],
        criteria: Callable[[list[Intersection[T]]], bool],
    ) -> list[Vec2]: ...
