from enum import Enum
from typing import Annotated, Literal, Union
from uuid import UUID

from flanker_core.models.components import CombatUnit, InitiativeState
from flanker_core.models.outcomes import AssaultOutcomes, FireEffect, FireOutcomes
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

    unit_id: UUID
    position: Vec2
    degree: float
    status: CombatUnit.Status
    is_friendly: bool
    firing_at: tuple[UUID, FireEffect] | None = None


class GameViewState(BaseModel, CamelCaseConfig):
    """Simplified view model of the game state."""

    class ObjectiveState(Enum):
        INCOMPLETE = "INCOMPLETE"
        COMPLETED = "COMPLETED"
        FAILED = "FAILED"

    objective_state: ObjectiveState
    has_initiative: bool
    squads: list[SquadModel]


class GameViewStateResponse(BaseModel, CamelCaseConfig):
    """Response model for actions contains view state and mutated game state."""

    view_state: GameViewState
    json_state: str


class MoveActionRequest(BaseModel, CamelCaseConfig):
    """Request model for a unit's move action."""

    action_type: Literal["MoveActionRequest"] = "MoveActionRequest"
    unit_id: UUID
    to: Vec2


class FireActionRequest(BaseModel, CamelCaseConfig):
    """Request model for a unit's fire action."""

    action_type: Literal["FireActionRequest"] = "FireActionRequest"
    unit_id: UUID
    target_id: UUID


class AssaultActionRequest(BaseModel, CamelCaseConfig):
    """Request model for a unit's assault action."""

    action_type: Literal["AssaultActionRequest"] = "AssaultActionRequest"
    unit_id: UUID
    target_id: UUID


class PivotActionRequest(BaseModel, CamelCaseConfig):
    """Request model for a unit's pivot action."""

    action_type: Literal["PivotActionRequest"] = "PivotActionRequest"
    unit_id: UUID
    to: Vec2


class TerrainModel(BaseModel, CamelCaseConfig):
    """Represents a view of terrain feature in the game."""

    terrain_id: UUID
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
    view_state: GameViewState


class PivotActionLog(BaseModel, CamelCaseConfig):
    log_type: Literal["PivotActionLog"] = "PivotActionLog"
    body: PivotActionRequest
    reactive_fire_outcome: FireOutcomes | None = None
    view_state: GameViewState


class FireActionLog(BaseModel, CamelCaseConfig):
    log_type: Literal["FireActionLog"] = "FireActionLog"
    body: FireActionRequest
    outcome: FireOutcomes | None = None
    view_state: GameViewState


class AssaultActionLog(BaseModel, CamelCaseConfig):
    log_type: Literal["AssaultActionLog"] = "AssaultActionLog"
    body: AssaultActionRequest
    outcome: AssaultOutcomes | None = None
    reactive_fire_outcome: FireOutcomes | None = None
    view_state: GameViewState


class AiWaypointConfigRequest(BaseModel, CamelCaseConfig):
    faction: InitiativeState.Faction
    points: list[Vec2]


ActionRequest = Annotated[
    Union[
        MoveActionRequest,
        PivotActionRequest,
        FireActionRequest,
        AssaultActionRequest,
    ],
    Field(discriminator="action_type"),
]


ActionLog = Annotated[
    Union[
        MoveActionLog,
        PivotActionLog,
        FireActionLog,
        AssaultActionLog,
    ],
    Field(discriminator="log_type"),
]
