from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from core.models.components import CombatUnit
from core.models.outcomes import AssaultOutcomes, FireOutcomes
from core.models.vec2 import Vec2
from webapi.models import CombatUnitsViewState


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