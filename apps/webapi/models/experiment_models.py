from flanker_ai.config_models import TranspositionScheme
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelCaseConfig:
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class TranspositionTestRequest(BaseModel, CamelCaseConfig):
    """Request model for transposition experiment tests."""

    state_a: str
    state_b: str
    key_methods: list[TranspositionScheme.ALL]


class TranspositionTestResponse(BaseModel, CamelCaseConfig):
    """Response model for transposition experiment tests."""

    key_is_same: bool


class TreePayoffRequest(BaseModel, CamelCaseConfig):
    """Request model for game-tree payoff value."""

    state: str


class TreePayoffResponse(BaseModel, CamelCaseConfig):
    """Response model for game-tree payoff value."""

    payoff_value: float
