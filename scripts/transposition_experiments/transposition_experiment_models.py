from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from flanker_ai.config_models import TranspositionScheme
from flanker_core.gamestate import GameState
from pydantic import BaseModel


class TranspositionTestResult(BaseModel):
    key_is_same: bool
    tree_a_value: float
    tree_b_value: float


class TranspositionExperimentSetConfig(BaseModel):
    """Input config model for entire transposition experiment-set run."""

    n_tests: int
    state_populating_methods: list[Literal["random", "perturbation"]]
    zobrist_key_methods: dict[str, list[TranspositionScheme.ALL]]
    max_workers: int
    target: Literal["local"] | str


@dataclass
class TranspositionExperiment:
    name: str
    state_populating_method: Literal["random", "perturbation"]
    key_methods: list[TranspositionScheme.ALL]
    n_tests: int


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
    key_method: list[TranspositionScheme.ALL]
