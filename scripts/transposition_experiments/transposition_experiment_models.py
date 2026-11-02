from dataclasses import dataclass
from typing import Literal

from flanker_ai.config_models import TranspositionScheme
from flanker_core.gamestate import GameState
from flanker_core.models.actions import Action
from pydantic import BaseModel


class TranspositionTestResult(BaseModel):
    key_is_same: bool
    result_is_same: bool


class TranspositionExperimentSetConfig(BaseModel):
    """Input config model for entire transposition experiment-set run."""

    n_tests: int
    state_populating_methods: list[Literal["random", "perturbation"]]
    # TODO: Should this key methods be combinable?
    # A single key generation can combine different key methods.
    zobrist_key_methods: list[TranspositionScheme.ALL]
    max_workers: int
    target: Literal["local"] | str


@dataclass(frozen=True)
class AiTreeResult:
    best_action: Action | None
    value: float


@dataclass
class TranspositionExperiment:
    name: str
    state_populating_method: Literal["random", "perturbation"]
    key_method: TranspositionScheme.ALL
    n_tests: int


class TranspositionExperimentMetadata(BaseModel):
    state_populating_method: Literal["random", "perturbation"]
    key_method: TranspositionScheme.ALL
    n_tests: int
    target_n_tests: int


@dataclass
class TranspositionTestRun:
    experiment_name: str
    state_a: GameState
    state_b: GameState
    key_method: TranspositionScheme.ALL
