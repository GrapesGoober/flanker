from typing import Literal

from flanker_ai.components import AiConfigComponent
from flanker_core.models.components import InitiativeState
from pydantic import BaseModel


class MatchResult(BaseModel):
    """Match result model for each recorded match run."""

    winner: InitiativeState.Faction | None
    total_runtime: float
    blue_search_sizes: list[int]
    red_search_sizes: list[int]


class ExperimentResult(BaseModel):
    """Result of an experiment run containing its match results."""

    n_matches: int
    blue_config: AiConfigComponent
    red_config: AiConfigComponent
    match_results: list[MatchResult]


class ExperimentSetConfig(BaseModel):
    """Input config model for entire experiment-set run."""

    scene_files: dict[str, str]
    scene_configs: list[str]
    blue_configs: list[str]
    red_configs: list[str]
    match_settings: list[str]
    n_matches: int
    max_workers: int
    target: Literal["local"] | str
