from typing import Literal

from flanker_ai.components import AiConfigComponent
from flanker_ai.policies.search_log_models import AiSearchLog
from flanker_core.models.components import InitiativeState
from pydantic import BaseModel


class MatchResult(BaseModel):
    """Match result model for each recorded match run."""

    winner: InitiativeState.Faction | None
    total_runtime_seconds: float
    search_logs: list[AiSearchLog]


class ExperimentMetadata(BaseModel):
    """Metadata of an experiment run."""

    n_matches: int
    blue_config: AiConfigComponent
    red_config: AiConfigComponent


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
