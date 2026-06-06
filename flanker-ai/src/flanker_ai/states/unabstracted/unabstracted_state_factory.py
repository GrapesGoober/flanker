import random
from typing import Iterable

from flanker_ai.config_models import PointsConfig, UnabstractedStateConfig
from flanker_ai.states.common.ai_points_expansion_service import (
    AiPointsExpansionService,
)
from flanker_ai.states.unabstracted.unabstracted_state import UnabstractedState, Vec2
from flanker_core.gamestate import GameState
from flanker_core.models.components import TerrainFeature, Transform
from flanker_core.utils.intersect_getter import IntersectGetter
from flanker_core.utils.linear_transform import LinearTransform

_MOVE_RANDOM_SIZE = 10


class UnabstractedStateFactory:
    @staticmethod
    def create_state(
        gs: GameState,
        config: UnabstractedStateConfig,
    ) -> UnabstractedState:

        move_candidates: list[Vec2] = []
        match config.move_candidates:
            case PointsConfig():
                move_candidates = AiPointsExpansionService.get_points(
                    gs=gs,
                    config=config.move_candidates,
                )

            case "RandomMoves":
                move_candidates = list(
                    UnabstractedStateFactory.get_random_coordinates(gs)
                )
        return UnabstractedState(gs, move_candidates)

    @staticmethod
    def get_random_coordinates(
        gs: GameState,
    ) -> Iterable[Vec2]:
        boundary_vertices: list[Vec2] = []
        mask = TerrainFeature.Flag.BOUNDARY
        for _, terrain, transform in gs.query(TerrainFeature, Transform):
            if terrain.flag & mask:
                boundary_vertices = LinearTransform.apply(
                    terrain.vertices,
                    transform,
                )
                if terrain.is_closed_loop:
                    boundary_vertices.append(boundary_vertices[0])
        min_x = int(min(v.x for v in boundary_vertices))
        max_x = int(max(v.x for v in boundary_vertices))
        min_y = int(min(v.y for v in boundary_vertices))
        max_y = int(max(v.y for v in boundary_vertices))

        for _ in range(_MOVE_RANDOM_SIZE):
            rand_x = random.randrange(min_x, max_x)
            rand_y = random.randrange(min_y, max_y)
            move_candidate = Vec2(rand_x, rand_y)
            if not IntersectGetter.is_inside(
                point=move_candidate,
                polygon=boundary_vertices,
            ):
                continue
            yield move_candidate
