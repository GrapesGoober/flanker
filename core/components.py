from dataclasses import dataclass
from enum import Enum, IntFlag, auto
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

    vertices: list[Vec2]
    flag: int = -1

    class Flag(IntFlag):
        """Bit flags for allowable terrain feature properties."""

        NONE = 0  # Important: Start with 0 for no flags
        OPAQUE = auto()
        WALKABLE = auto()
        DRIVABLE = auto()
        WATER = auto()
        HILL = auto()
