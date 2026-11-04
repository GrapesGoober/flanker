from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from flanker_ai.config_models import TranspositionScheme
from flanker_core.gamestate import GameState
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class TranspositionTestResult(BaseModel):
    key_is_same: bool
    action_a_value: float
    action_b_value: float


class TranspositionExperimentSetConfig(BaseModel):
    """Input config model for entire transposition experiment-set run."""

    target_n_tests: int
    state_populating_methods: list[Literal["random", "perturbation"]]
    zobrist_key_methods: dict[str, list[TranspositionScheme.ALL]]
    max_workers: int
    target: Literal["local"] | str


@dataclass
class TranspositionExperiment:
    name: str
    state_populating_method: Literal["random", "perturbation"]
    key_methods: list[TranspositionScheme.ALL]
    target: Literal["local"] | str


class TranspositionExperimentMetadata(BaseModel):
    state_populating_method: Literal["random", "perturbation"]
    key_methods: list[TranspositionScheme.ALL]
    n_tests: int
    target_n_tests: int


@dataclass
class TranspositionTestRun:
    experiment_name: str
    state_a: GameState
    state_b: GameState
    key_methods: list[TranspositionScheme.ALL]
    target: Literal["local"] | str


class _CamelCaseConfig:
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class ApiTranspositionTestRequest(BaseModel, _CamelCaseConfig):
    """Request model for transposition experiment tests."""

    state_a: str
    state_b: str
    key_methods: list[TranspositionScheme.ALL]


class ApiTranspositionTestResponse(BaseModel, _CamelCaseConfig):
    """Response model for transposition experiment tests."""

    key_is_same: bool
    action_a_value: float
    action_b_value: float
