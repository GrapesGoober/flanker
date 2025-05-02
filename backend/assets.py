from dataclasses import dataclass
from enum import Enum
from core.components import MovementControls, TerrainFeature, CombatUnit
from core.vec2 import Vec2
from core.gamestate import GameState


@dataclass
class SquadModel:
    unit_id: int
    position: Vec2
    status: CombatUnit.Status


@dataclass
class TerrainModel:
    feature_id: int
    vertices: list[Vec2]
    terrain_type: "Types"

    class Types(Enum):
        """Supported terrain types."""

        FOREST = "FOREST"
        ROAD = "ROAD"
        FIELD = "FIELD"
        WATER = "WATER"


def get_terrain_flags(terrain_type: TerrainModel.Types) -> TerrainFeature.Flag:
    match terrain_type:
        case TerrainModel.Types.FOREST:
            return TerrainFeature.Flag.OPAQUE | TerrainFeature.Flag.WALKABLE
        case TerrainModel.Types.ROAD:
            return TerrainFeature.Flag.WALKABLE | TerrainFeature.Flag.DRIVABLE
        case TerrainModel.Types.FIELD:
            return TerrainFeature.Flag.WALKABLE
        case TerrainModel.Types.WATER:
            return TerrainFeature.Flag.WATER
        case _:
            raise ValueError(f"Unknown terrain type: {terrain_type}")


def get_terrain_type(flags: int) -> TerrainModel.Types:
    if flags == (TerrainFeature.Flag.OPAQUE | TerrainFeature.Flag.WALKABLE):
        return TerrainModel.Types.FOREST
    elif flags == (TerrainFeature.Flag.WALKABLE | TerrainFeature.Flag.DRIVABLE):
        return TerrainModel.Types.ROAD
    elif flags == TerrainFeature.Flag.WALKABLE:
        return TerrainModel.Types.FIELD
    elif flags == TerrainFeature.Flag.WATER:
        return TerrainModel.Types.WATER
    else:
        raise ValueError(f"Unknown terrain flags: {flags}")


@staticmethod
def add_squad(gs: GameState, pos: Vec2) -> None:
    gs.add_entity(MovementControls(), CombatUnit(position=pos))


@staticmethod
def add_terrain(
    gs: GameState, vertices: list[Vec2], terrain_type: TerrainModel.Types
) -> None:
    gs.add_entity(
        TerrainFeature(
            vertices=vertices,
            flag=get_terrain_flags(terrain_type),
        ),
    )
