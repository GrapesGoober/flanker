from typing import Literal

from flanker_ai.agents.ai_random_heuristic_agent import RandomHeuristicLog
from flanker_ai.ai_action_result import AiActionResult
from flanker_ai.config_models import AiConfigComponent
from flanker_ai.search_policies.search_log_models import AiSearchLog
from flanker_core.models.components import InitiativeState
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class MatchResult(BaseModel):
    """Match result model for each recorded match run."""

    winner: InitiativeState.Faction | None
    total_runtime_seconds: float
    action_results: list[
        AiActionResult[AiSearchLog] | AiActionResult[RandomHeuristicLog]
    ]


class ExperimentMetadata(BaseModel):
    """Metadata of an experiment run."""

    n_matches: int
    blue_config: AiConfigComponent
    red_config: AiConfigComponent


class ExperimentSetConfig(BaseModel):
    """Input config model for entire experiment-set run."""

    scene_configs: list[str]
    blue_configs: list[str]
    red_configs: list[str]
    match_settings: list[str]
    n_matches: int
    max_workers: int
    target: Literal["local"] | str


class SceneManifest(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    quick_access: dict[str, list[str]]
    scene_paths: dict[str, str]
