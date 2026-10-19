from typing import Annotated, Literal, Union
from uuid import UUID

from flanker_core.models.outcomes import AssaultOutcomes, FireOutcomes
from flanker_core.models.vec2 import Vec2
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from webapi.models.state_models import GameViewState


class CamelCaseConfig:
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class MoveActionModel(BaseModel, CamelCaseConfig):
    """API model for a unit's move action."""

    action_type: Literal["MoveActionModel"] = "MoveActionModel"
    unit_id: UUID
    to: Vec2


class FireActionModel(BaseModel, CamelCaseConfig):
    """API model for a unit's fire action."""

    action_type: Literal["FireActionModel"] = "FireActionModel"
    unit_id: UUID
    target_id: UUID


class AssaultActionModel(BaseModel, CamelCaseConfig):
    """API model for a unit's assault action."""

    action_type: Literal["AssaultActionModel"] = "AssaultActionModel"
    unit_id: UUID
    target_id: UUID


class PivotActionModel(BaseModel, CamelCaseConfig):
    """API model for a unit's pivot action."""

    action_type: Literal["PivotActionModel"] = "PivotActionModel"
    unit_id: UUID
    to: Vec2


class MoveActionLog(BaseModel, CamelCaseConfig):
    log_type: Literal["MoveActionLog"] = "MoveActionLog"
    body: MoveActionModel
    reactive_fire_outcomes: list[FireOutcomes]
    view_state: GameViewState


class PivotActionLog(BaseModel, CamelCaseConfig):
    log_type: Literal["PivotActionLog"] = "PivotActionLog"
    body: PivotActionModel
    reactive_fire_outcomes: list[FireOutcomes]
    view_state: GameViewState


class FireActionLog(BaseModel, CamelCaseConfig):
    log_type: Literal["FireActionLog"] = "FireActionLog"
    body: FireActionModel
    outcome: FireOutcomes | None
    view_state: GameViewState


class AssaultActionLog(BaseModel, CamelCaseConfig):
    log_type: Literal["AssaultActionLog"] = "AssaultActionLog"
    body: AssaultActionModel
    outcome: AssaultOutcomes | None
    reactive_fire_outcomes: list[FireOutcomes]
    view_state: GameViewState


type ActionModel = Annotated[
    Union[
        MoveActionModel,
        PivotActionModel,
        FireActionModel,
        AssaultActionModel,
    ],
    Field(discriminator="action_type"),
]


type ActionLog = Annotated[
    Union[
        MoveActionLog,
        PivotActionLog,
        FireActionLog,
        AssaultActionLog,
    ],
    Field(discriminator="log_type"),
]
