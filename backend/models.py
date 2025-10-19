from enum import Enum

from pydantic.alias_generators import to_camel
from core.components import CombatUnit
from core.utils.vec2 import Vec2
from core.action_models import (
    AssaultActionResult,
    FireActionResult,
    MoveActionResult,
)
from pydantic import BaseModel, ConfigDict


class CamelCaseConfig:
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class SquadModel(BaseModel, CamelCaseConfig):
    """Represents a view of a single squad in the game."""

    unit_id: int
    position: Vec2
    status: CombatUnit.Status
    is_friendly: bool
    no_fire: bool


class CombatUnitsViewState(BaseModel, CamelCaseConfig):
    """View state for all combat units in the game."""

    class ObjectiveState(Enum):
        INCOMPLETE = "INCOMPLETE"
        COMPLETED = "COMPLETED"
        FAILED = "FAILED"

    objective_state: ObjectiveState
    has_initiative: bool
    squads: list[SquadModel]


class MoveActionRequest(BaseModel, CamelCaseConfig):
    """Request model for a unit's move action."""

    unit_id: int
    to: Vec2


class FireActionRequest(BaseModel, CamelCaseConfig):
    """Request model for a unit's fire action."""

    unit_id: int
    target_id: int


class AssaultActionRequest(BaseModel, CamelCaseConfig):
    """Request model for a unit's assault action."""

    unit_id: int
    target_id: int


class TerrainModel(BaseModel, CamelCaseConfig):
    """Represents a view of terrain feature in the game."""

    terrain_id: int
    position: Vec2
    degrees: float
    vertices: list[Vec2]
    terrain_type: "Types"

    class Types(Enum):
        """Supported terrain types."""

        FOREST = "FOREST"
        ROAD = "ROAD"
        FIELD = "FIELD"
        WATER = "WATER"
        BUILDING = "BUILDING"


class ActionType(str, Enum):
    MOVE = "move"
    FIRE = "fire"
    ASSAULT = "assault"


class MoveActionLog(BaseModel, CamelCaseConfig):
    type: ActionType = ActionType.MOVE
    body: MoveActionRequest
    result: MoveActionResult
    unit_state: CombatUnitsViewState


class FireActionLog(BaseModel, CamelCaseConfig):
    type: ActionType = ActionType.FIRE
    body: FireActionRequest
    result: FireActionResult
    unit_state: CombatUnitsViewState


class AssaultActionLog(BaseModel, CamelCaseConfig):
    type: ActionType = ActionType.ASSAULT
    body: AssaultActionRequest
    result: AssaultActionResult
    unit_state: CombatUnitsViewState


ActionLog = MoveActionLog | FireActionLog | AssaultActionLog
