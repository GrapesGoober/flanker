from backend.domain import TerrainModel, add_terrain, add_squad
from core.vec2 import Vec2


def create_scene() -> None:
    add_squad(Vec2(120, 160))
    add_squad(Vec2(180, 260))

    add_terrain(
        [
            Vec2(100, 100),
            Vec2(130, 70),
            Vec2(170, 80),
            Vec2(200, 100),
            Vec2(220, 140),
            Vec2(200, 180),
            Vec2(160, 190),
            Vec2(110, 160),
            Vec2(100, 100),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )
