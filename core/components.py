from dataclasses import dataclass
from enum import Enum
from core.terrain_types import TerrainType
from core.vec2 import Vec2


@dataclass
class Transform:
    """Component for a transformation of an entity."""

    position: Vec2


@dataclass
class UnitCondition:
    """Component for combat unit status conditions."""

    class Status(Enum):
        ACTIVE = "ACTIVE"
        SUPPRESSED = "SUPPRESSED"

    status: Status = Status.ACTIVE


@dataclass
class MovementControls:
    """Component for movement controls configurations."""

    ...


@dataclass
class TerrainFeature:
    """Component for terrain feature polygon."""

    points: list[Vec2]
    terrain_type: TerrainType
