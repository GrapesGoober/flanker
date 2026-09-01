import json
import random
from copy import deepcopy
from dataclasses import dataclass, is_dataclass
from inspect import isclass
from itertools import product
from multiprocessing.pool import Pool, ThreadPool
from pathlib import Path
from typing import Any, Iterable, Literal
from uuid import UUID

import requests
from flanker_ai.ai_agent import AiAgent
from flanker_ai.ai_match import AiMatch
from flanker_ai.components import AiConfigComponent
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.models.components import InitiativeState
from flanker_core.serializer import Serializer
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class MatchResult(BaseModel):
    """Match result model for each recorded match run."""

    winner: InitiativeState.Faction | None
    total_runtime: float
    blue_search_sizes: list[int]
    red_search_sizes: list[int]


class MatchResultApiResponse(BaseModel):
    """Response model from WebAPI, kept separate from MatchResult."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    winner: InitiativeState.Faction | None
    total_runtime: float
    blue_search_sizes: list[int]
    red_search_sizes: list[int]


class ExperimentResult(BaseModel):
    """Result of an experiment run containing its match results."""

    n_matches: int
    match_results: list[MatchResult]


class ExperimentSetConfig(BaseModel):
    """Input config model for entire experiment-set run."""

    scene_configs: dict[str, str]
    blue_configs: dict[str, str]
    red_configs: dict[str, str]
    match_settings: dict[str, str]
    n_matches: int
    max_workers: int
    target: Literal["local"] | str


@dataclass
class ExperimentConfig:
    """Input config model for running a many matches."""

    name: str
    gs: GameState
    n_matches: int
    target: Literal["local"] | str


@dataclass
class MatchConfig:
    """Input config model for running a single match."""

    name: str
    gs: GameState
    n_matches: int
    target: Literal["local"] | str


def main() -> None:
    results_root_path = "./scripts/outputs/experiment-results/"

    experiment_set = get_config(
        config_path="./scripts/configs/experiment-config.json",
    )
    experiments = get_experiments(experiment_set)
    matches = get_matches(experiments, results_root_path)
    random.shuffle(matches)

    # For local, parallelize using CPU.
    # For running this in cloud, concurrent using threads.
    pool_type: type[Pool] | type[ThreadPool]
    match experiment_set.target:
        case "local":
            pool_type = Pool
        case _:
            pool_type = ThreadPool

    # Run this in parallel
    with pool_type(processes=experiment_set.max_workers) as p:
        results = p.imap_unordered(run_match, matches)
        for match_result in results:
            result, match_config = match_result
            print(f"    {match_config.name} done, tallying")
            experiment_result = get_results(
                experiment_name=match_config.name,
                results_root_path=results_root_path,
            )
            if experiment_result.n_matches == match_config.n_matches:
                continue
            match_results = experiment_result.match_results
            match_results.append(result)
            experiment_result.n_matches = len(match_results)
            save_results(
                experiment_name=match_config.name,
                result=experiment_result,
                results_root_path=results_root_path,
            )


def get_config(config_path: str) -> ExperimentSetConfig:
    with open(config_path, "r") as f:
        return ExperimentSetConfig(**json.loads(f.read()))


def run_match(
    match_config: MatchConfig,
) -> tuple[MatchResult, MatchConfig]:
    print(f"Running match {match_config.name}")

    # Run locally if config says so
    if match_config.target == "local":
        result = AiMatch.run_match(match_config.gs)

    # Otherwise, assume the match.target is a Flanker WebAPI URL
    else:
        scene_data = Serializer.serialize(
            entities=match_config.gs.dump(),
            component_types=list(get_component_types()),
        )
        r = requests.post(
            f"{match_config.target}/api/ai-play",
            data=scene_data,
        )
        if 300 <= r.status_code <= 600:
            raise Exception(f"Request had {r.status_code} error: {r.text}")
        result = MatchResultApiResponse(**r.json())

    return (
        MatchResult(
            winner=result.winner,
            total_runtime=result.total_runtime,
            blue_search_sizes=result.blue_search_sizes,
            red_search_sizes=result.red_search_sizes,
        ),
        match_config,
    )


def get_experiments(
    experiment_set: ExperimentSetConfig,
) -> list[ExperimentConfig]:
    return [
        ExperimentConfig(
            name="-".join(name for name, _ in combination),
            gs=get_game_state(list(path for _, path in combination)),
            n_matches=experiment_set.n_matches,
            target=experiment_set.target,
        )
        for combination in product(
            experiment_set.scene_configs.items(),
            experiment_set.blue_configs.items(),
            experiment_set.red_configs.items(),
            experiment_set.match_settings.items(),
        )
    ]


def get_matches(
    experiments: list[ExperimentConfig],
    results_root_path: str,
) -> list[MatchConfig]:
    matches: list[MatchConfig] = []
    for experiment in experiments:
        current_tally = get_results(
            experiment.name,
            results_root_path,
        )
        remaining_matches = max(
            0,
            experiment.n_matches - current_tally.n_matches,
        )
        gs = deepcopy(experiment.gs)
        for _ in range(remaining_matches):
            matches.append(
                MatchConfig(
                    name=experiment.name,
                    gs=gs,
                    n_matches=experiment.n_matches,
                    target=experiment.target,
                )
            )

    return matches


def get_game_state(
    paths: list[str],
) -> GameState:
    component_types = list(get_component_types())
    entities: dict[UUID, Any] = {}
    for path in paths:
        with open(path, "r") as f:
            entities.update(
                Serializer.deserialize(
                    json_data=f.read(),
                    component_types=component_types,
                )
            )

    gs = GameState.load(entities)
    AiAgent.get_agent(gs, InitiativeState.Faction.BLUE)
    AiAgent.get_agent(gs, InitiativeState.Faction.RED)
    return gs


def get_component_types() -> Iterable[type]:
    for _, cls in vars(components).items():
        if isclass(cls) and is_dataclass(cls):
            yield cls
    yield AiConfigComponent


def get_results(
    experiment_name: str,
    results_root_path: str,
) -> ExperimentResult:
    file_path = f"{results_root_path}{experiment_name}.json"
    if not Path(file_path).is_file():
        return ExperimentResult(
            n_matches=0,
            match_results=[],
        )

    with open(file_path, "r") as f:
        # This file reading is unreliable... need better file IO?
        file_data = f.read()
        if file_data == "":
            raise Exception(f"{file_path} file fmpty?!")
        return ExperimentResult.model_validate_json(file_data)


def save_results(
    experiment_name: str,
    result: ExperimentResult,
    results_root_path: str,
) -> None:
    file_path = f"{results_root_path}{experiment_name}.json"
    with open(file_path, "w") as f:
        f.write(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
