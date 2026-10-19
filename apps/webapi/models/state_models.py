from enum import Enum
from uuid import UUID

from flanker_core.models.components import CombatUnit, InitiativeState
from flanker_core.models.outcomes import FireEffect
from flanker_core.models.vec2 import Vec2
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelCaseConfig:
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class SceneManifest(BaseModel, CamelCaseConfig):
    scene_paths: dict[str, str]


class SceneManifestResponse(BaseModel, CamelCaseConfig):
    scene_names: list[str]


class SquadModel(BaseModel, CamelCaseConfig):
    """Represents a view of a single squad in the game."""

    unit_id: UUID
    position: Vec2
    degrees: float
    status: CombatUnit.Status
    is_friendly: bool
    fov_degrees: float | None
    firing_at: tuple[UUID, FireEffect] | None


class FireEffectPair(BaseModel, CamelCaseConfig):
    position_a: Vec2
    position_b: Vec2
    fire_effect_a: FireEffect | None
    fire_effect_b: FireEffect | None


class GameViewState(BaseModel, CamelCaseConfig):
    """Simplified view model of the game state."""

    class ObjectiveState(Enum):
        INCOMPLETE = "INCOMPLETE"
        COMPLETED = "COMPLETED"
        FAILED = "FAILED"

    objective_state: ObjectiveState
    has_initiative: bool
    squads: list[SquadModel]
    fire_effect_pairs: list[FireEffectPair]


class GameViewStateResponse(BaseModel, CamelCaseConfig):
    """Response model for actions contains view state and mutated game state."""

    view_state: GameViewState
    json_state: str


class TerrainType(Enum):
    """Supported terrain types."""

    FOREST = "FOREST"
    ROAD = "ROAD"
    FIELD = "FIELD"
    WATER = "WATER"
    BUILDING = "BUILDING"


class TerrainModel(BaseModel, CamelCaseConfig):
    """Represents a view of terrain feature in the game."""

    terrain_id: UUID
    position: Vec2
    degrees: float
    vertices: list[Vec2]
    terrain_type: TerrainType


class MapViewState(BaseModel, CamelCaseConfig):
    """Simplified view model of the game map."""

    terrains: list[TerrainModel]
    boundary: list[Vec2]


class AiSearchLogModel(BaseModel, CamelCaseConfig):
    tree_size: int
    tree_depth: int


class AiActionResultModel(BaseModel, CamelCaseConfig):
    faction: InitiativeState.Faction
    action_runtime_seconds: float
    policy_log: AiSearchLogModel | None


class AiMatchResponseModel(BaseModel, CamelCaseConfig):
    """Response model for AI match contains match result and final game state."""

    winner: InitiativeState.Faction | None
    total_runtime_seconds: float
    action_results: list[AiActionResultModel]
    json_state: str


class AiWaypointConfigRequestModel(BaseModel, CamelCaseConfig):
    faction: InitiativeState.Faction
    points: list[Vec2]
