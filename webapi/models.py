from enum import Enum
from typing import Annotated, Literal, Union

from flanker_core.models.components import CombatUnit
from flanker_core.models.outcomes import AssaultOutcomes, FireOutcomes
from flanker_core.models.vec2 import Vec2
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


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


class MoveActionLog(BaseModel, CamelCaseConfig):
    log_type: Literal["MoveActionLog"] = "MoveActionLog"
    body: MoveActionRequest
    reactive_fire_outcome: FireOutcomes | None = None
    unit_state: CombatUnitsViewState


class FireActionLog(BaseModel, CamelCaseConfig):
    log_type: Literal["FireActionLog"] = "FireActionLog"
    body: FireActionRequest
    outcome: FireOutcomes | None = None
    unit_state: CombatUnitsViewState


class AssaultActionLog(BaseModel, CamelCaseConfig):
    log_type: Literal["AssaultActionLog"] = "AssaultActionLog"
    body: AssaultActionRequest
    outcome: AssaultOutcomes | None = None
    reactive_fire_outcome: FireOutcomes | None = None
    unit_state: CombatUnitsViewState


ActionLog = Annotated[
    Union[MoveActionLog, FireActionLog, AssaultActionLog],
    Field(discriminator="log_type"),
]
