from dataclasses import dataclass
from enum import Enum
from core.components import CombatUnit
from core.utils.vec2 import Vec2


@dataclass
class SquadModel:
    """Represents a single squad in the game."""

    unit_id: int
    position: Vec2
    status: CombatUnit.Status
    is_friendly: bool


@dataclass
class CombatUnitsViewState:
    """View state for all combat units in the game."""

    has_initiative: bool
    squads: list[SquadModel]


@dataclass
class MoveActionRequest:
    """Request model for moving a unit."""

    unit_id: int
    to: Vec2


@dataclass
class TerrainModel:
    """Represents a terrain feature in the game."""

    feature_id: int
    vertices: list[Vec2]
    terrain_type: "Types"

    class Types(Enum):
        """Supported terrain types."""

        FOREST = "FOREST"
        ROAD = "ROAD"
        FIELD = "FIELD"
        WATER = "WATER"
        BUILDING = "BUILDING"
