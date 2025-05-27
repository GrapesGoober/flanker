from dataclasses import dataclass
from enum import Enum, IntFlag, auto
from core.vec2 import Vec2


@dataclass
class Transform:
    """Component for 2D linear transformations."""

    position: Vec2


@dataclass
class CombatUnit:
    """Component for combat unit status conditions."""

    class Status(Enum):
        ACTIVE = "ACTIVE"
        SUPPRESSED = "SUPPRESSED"

    command_id: int
    status: Status = Status.ACTIVE


@dataclass
class CommandUnit:
    """Component for commanding unit."""

    class Level(Enum):
        PLT = "PLT"
        COY = "COY"

    level: Level = Level.PLT
    has_initiative: bool = True


@dataclass
class MoveControls:
    """Component for movement controls configurations."""

    class MoveType(Enum):
        FOOT = "FOOT"
        WHEEL = "WHEEL"
        TRACK = "TRACK"

    move_type: MoveType = MoveType.FOOT
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
