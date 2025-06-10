from backend.models import TerrainModel
from backend.squad import SquadController
from backend.terrain import TerrainController
from core.vec2 import Vec2
from core.gamestate import GameState


def new_scene() -> GameState:
    """Initialize and return a `GameState` instance with predefined entities."""
    gs = GameState()

    # Add squads
    command = SquadController.add_command(gs, Vec2(100, 120))
    SquadController.add_squad(gs, Vec2(120, 160), command)
    SquadController.add_squad(gs, Vec2(180, 260), command)

    # Add terrains
    TerrainController.add_terrain(
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

    return gs
