from dataclasses import dataclass
from enum import Enum
from vec2 import Vec2


@dataclass
class Transform:
    position: Vec2


@dataclass
class UnitCondition:

    class Status(Enum):
        ACTIVE = "ACTIVE"
        SUPPRESSED = "SUPPRESSED"

    status: Status = Status.ACTIVE


@dataclass
class MovementControls: ...


@dataclass
class TerrainFeature:
    vertices: list[Vec2]
    flag: int = -1
