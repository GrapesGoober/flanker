from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from flanker_ai.config_models import SearchPolicyConfig, TranspositionScheme
from flanker_core.gamestate import GameState
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class TranspositionTestResult(BaseModel):
    key_is_same: bool
    tree_a_payoff: float
    tree_b_payoff: float


class StatePopulatingMethod:

    @dataclass
    class Random:
        type: Literal["random"]

    @dataclass
    class Perturbation:
        type: Literal["perturbation"]
        size: float

    ALL = Random | Perturbation


class TranspositionExperimentSetConfig(BaseModel):
    """Input config model for entire transposition experiment-set run."""

    target_n_tests: int
    maps: list[str]
    state_populating_methods: dict[str, StatePopulatingMethod.ALL]
    transposition_key_methods: dict[str, list[TranspositionScheme.ALL]]
    max_workers: int
    game_tree_method: SearchPolicyConfig
    target: Literal["local"] | str


@dataclass
class InputStatePair:
    state_a: GameState
    state_b: GameState
    tree_a_payoff: float
    tree_b_payoff: float


@dataclass
class InputStatePairConfig:
    name: str
    map_state: GameState
    state_method: StatePopulatingMethod.ALL
    ai_config: SearchPolicyConfig


class TranspositionExperimentMetadata(BaseModel):
    name: str
    state_populating_method_name: str
    state_populating_method: StatePopulatingMethod.ALL
    key_method_name: str
    key_methods: list[TranspositionScheme.ALL]
    map_name: str
    n_tests: int
    target_n_tests: int


@dataclass
class TranspositionExperiment:
    state_sequence: list[InputStatePair]
    key_methods: list[TranspositionScheme.ALL]
    target: Literal["local"] | str
    metadata: TranspositionExperimentMetadata


@dataclass
class TranspositionTestRun:
    experiment_name: str
    state_a: GameState
    state_b: GameState
    tree_a_payoff: float
    tree_b_payoff: float
    key_methods: list[TranspositionScheme.ALL]
    target: Literal["local"] | str


class _ApiCamelCaseConfig:
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class ApiTranspositionTestRequest(BaseModel, _ApiCamelCaseConfig):
    """Request model for transposition experiment tests."""

    state_a: str
    state_b: str
    key_methods: list[TranspositionScheme.ALL]


class ApiTranspositionTestResponse(BaseModel, _ApiCamelCaseConfig):
    """Response model for transposition experiment tests."""

    key_is_same: bool
