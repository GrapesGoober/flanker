from dataclasses import dataclass
from typing import Iterable, override

from flanker_core.gamestate import GameState
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.intersect_system import Intersection, IntersectSystem


@dataclass
class _IntersectCacheKey:
    start: Vec2
    end: Vec2
    mask: int


@dataclass
class _IntersectionCacheComponent:
    terrain_intersects_cache: dict[
        _IntersectCacheKey,
        list[Intersection],
    ]


class WaypointsIntersectSystem(IntersectSystem):
    @staticmethod
    @override
    def get(
        gs: GameState,
        start: Vec2,
        end: Vec2,
        mask: int = -1,
    ) -> Iterable[Intersection]:
        # This override is intended for move action validation.
        # The set of possible inputs (start, end, mask) for
        # terrain operations are finite, and thus cachable

        if entities := gs.query(_IntersectionCacheComponent):
            _, cache_component = entities[0]
        else:
            gs.add_entity(
                cache_component := _IntersectionCacheComponent({}),
            )

        key = _IntersectCacheKey(start, end, mask)
        if key in cache_component.terrain_intersects_cache:
            return cache_component.terrain_intersects_cache[key]

        # Cache miss, add a new entry
        terrain_intersections = list(
            IntersectSystem.get(
                gs,
                start,
                end,
                mask,
            ),
        )
        cache_component.terrain_intersects_cache[key] = terrain_intersections
        return terrain_intersections
