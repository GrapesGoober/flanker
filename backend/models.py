from enum import Enum

from pydantic import BaseModel
from core.components import CombatUnit
from core.utils.vec2 import Vec2


class SquadModel(BaseModel):
    """Represents a view of a single squad in the game."""

    unit_id: int
    position: Vec2
    status: CombatUnit.Status
    is_friendly: bool
    no_fire: bool


class CombatUnitsViewState(BaseModel):
    """View state for all combat units in the game."""

    has_initiative: bool
    squads: list[SquadModel]


class MoveActionRequest(BaseModel):
    """Request model for a unit's move action."""

    unit_id: int
    to: Vec2


class FireActionRequest(BaseModel):
    """Request model for a unit's fire action."""

    unit_id: int
    target_id: int


class TerrainModel(BaseModel):
    """Represents a view of terrain feature in the game."""

    feature_id: int
    position: Vec2
    angle: float
    vertices: list[Vec2]
    terrain_type: "Types"

    class Types(Enum):
        """Supported terrain types."""

        FOREST = "FOREST"
        ROAD = "ROAD"
        FIELD = "FIELD"
        WATER = "WATER"
        BUILDING = "BUILDING"


class TerrainTransformModel(BaseModel):
    """Represents the transformation data of a terrain feature."""

    feature_id: int
    position: Vec2
    angle: float
