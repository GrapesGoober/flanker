from dataclasses import dataclass
from typing import Iterable
from uuid import UUID

from flanker_core.gamestate import GameState
from flanker_core.models.components import TerrainFeature, Transform
from flanker_core.models.vec2 import Vec2
from flanker_core.utils.intersect_getter import IntersectGetter
from flanker_core.utils.linear_transform import LinearTransform


@dataclass
class Intersection:
    """Represents intersection between line and terrain feature."""

    terrain: TerrainFeature
    terrain_id: UUID


class IntersectSystem:
    """ECS system for finding line and terrain feature intersections."""

    @staticmethod
    def get(
        gs: GameState, start: Vec2, end: Vec2, mask: int = -1
    ) -> Iterable[Intersection]:
        """
        Returns what terrains intersects with the given line segment.
        The intersections are arbitrary and is not sorted.
        """

        all_intersections: list[Intersection] = []
        for id, terrain, transform in gs.query(TerrainFeature, Transform):
            if (terrain.flag & mask) == 0:
                continue
            vertices = LinearTransform.apply(terrain.vertices, transform)
            if terrain.is_closed_loop:
                vertices.append(vertices[0])
            intersections = IntersectGetter.get_intersects(
                line=(start, end),
                polyline=vertices,
            )
            for _ in intersections:
                all_intersections.append(
                    Intersection(
                        terrain=terrain,
                        terrain_id=id,
                    )
                )

        return all_intersections
