from dataclasses import dataclass
from enum import Enum

import esper

from core.components import MovementControls, TerrainFeature, Transform, UnitCondition
from core.vec2 import Vec2


@dataclass
class SquadModel:
    unit_id: int
    position: Vec2
    status: UnitCondition.Status


@dataclass
class TerrainModel:
    feature_id: int
    position: Vec2
    vertices: list[Vec2]
    terrain_type: "Types"

    class Types(Enum):
        """Supported terrain types."""

        FOREST = "FOREST"
        ROAD = "ROAD"
        FIELD = "FIELD"
        WATER = "WATER"


# Mapping table for TerrainType to TerrainFlag and vice versa
TERRAIN_FLAGS: dict[TerrainModel.Types, TerrainFeature.Flag] = {
    TerrainModel.Types.FOREST: TerrainFeature.Flag.OPAQUE
    | TerrainFeature.Flag.WALKABLE,
    TerrainModel.Types.ROAD: TerrainFeature.Flag.WALKABLE
    | TerrainFeature.Flag.DRIVABLE,
    TerrainModel.Types.FIELD: TerrainFeature.Flag.WALKABLE,
    TerrainModel.Types.WATER: TerrainFeature.Flag.WATER,
}


@staticmethod
def add_squad(pos: Vec2) -> None:
    esper.create_entity(Transform(position=pos), MovementControls(), UnitCondition())


@staticmethod
def add_terrain(vertices: list[Vec2], terrain_type: TerrainModel.Types) -> None:
    esper.create_entity(
        Transform(Vec2(0, 0)),
        TerrainFeature(
            vertices=vertices,
            flag=TERRAIN_FLAGS[terrain_type],
        ),
    )
