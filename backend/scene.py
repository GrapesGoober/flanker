from backend.assets import TerrainModel, add_squad, add_terrain
from core.vec2 import Vec2
from core.gamestate import GameState


def create_gamestate() -> GameState:
    """Initialize and return a `GameState` instance with predefined entities."""
    gs = GameState()

    # Add squads
    add_squad(gs, Vec2(120, 160))
    add_squad(gs, Vec2(180, 260))

    # Add terrains
    add_terrain(
        gs,
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
    add_terrain(
        gs,
        [
            Vec2(308, 95),
            Vec2(313, 135),
            Vec2(346, 174),
            Vec2(389, 183),
            Vec2(447, 172),
            Vec2(488, 201),
            Vec2(507, 246),
            Vec2(526, 284),
            Vec2(580, 293),
            Vec2(628, 267),
            Vec2(646, 195),
            Vec2(655, 144),
            Vec2(632, 80),
            Vec2(574, 46),
            Vec2(504, 26),
            Vec2(430, 20),
            Vec2(368, 30),
            Vec2(334, 50),
        ],
        terrain_type=TerrainModel.Types.FOREST,
    )

    return gs
