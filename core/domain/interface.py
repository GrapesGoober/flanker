"""
Interface classes for events and enums for Entities to communicate.
"""

from dataclasses import dataclass
from enum import Enum
from systems.vec2 import Vec2


@dataclass
class MoveActionInput:
    unit_id: int
    position: Vec2


class UnitState(Enum):
    ACTIVE = "ACTIVE"
    SUPPRESSED = "SUPPRESSED"


@dataclass
class RifleSquadGetInput:
    @dataclass
    class Response:
        unit_id: int
        position: Vec2
        state: UnitState


class TerrainType(Enum):
    FOREST = "FOREST"
    ROAD = "ROAD"
    FIELD = "FIELD"


@dataclass
class TerrainFeatureGetInput:
    @dataclass
    class Response:
        terrain_type: TerrainType
        coordinates: list[Vec2]


@dataclass
class LosCheckEvent:
    parent_id: int
    position: Vec2

    @dataclass
    class Response:
        parent_id: int
