import json
import random
from copy import deepcopy
from dataclasses import dataclass, is_dataclass
from inspect import isclass
from itertools import product
from multiprocessing.pool import Pool, ThreadPool
from pathlib import Path
from typing import Any, Iterable
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
    winner: InitiativeState.Faction | None
    total_runtime: float
    blue_search_sizes: list[int]
    red_search_sizes: list[int]


class ExperimentResult(BaseModel):
    n_matches: int
    blue_config: AiConfigComponent
    red_config: AiConfigComponent
    match_results: list[MatchResult]


class ExperimentRunConfig(BaseModel):
    url: str
    scenes: list[str]
    parallelization: int
    size_to_run: int


@dataclass
class ExperimentConfig:
    experiment_run_config: ExperimentRunConfig
    name: str
    gs: GameState
    n_matches: int


@dataclass
class ExperimentSetConfig:
    scene_configs: dict[str, str]
    blue_configs: dict[str, str]
    red_configs: dict[str, str]
    match_settings: dict[str, str]
    n_matches: int
    max_workers: int


class CamelCaseConfig:
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class AiMatchResponse(BaseModel, CamelCaseConfig):
    """Response model from WebAPI."""

    winner: InitiativeState.Faction | None
    total_runtime: float
    blue_search_sizes: list[int]
    red_search_sizes: list[int]


FOLDER = "./scripts/outputs/experiment-results/"


def main() -> None:
    my_run = ExperimentSetConfig(
        scene_configs={
            "scene-1": "./scenes/experiment-scene-1.json",
            "scene-2": "./scenes/experiment-scene-2.json",
        },
        blue_configs={
            # "blue-analysis": "./scenes/experiment-blue-analysis.json",
            # "blue-mcts": "./scenes/experiment-blue-mcts.json",
            # "blue-grid": "./scenes/experiment-blue-grid.json",
            "blue-rh": "./scenes/experiment-blue-rh.json",
        },
        red_configs={
            # "red-analysis": "./scenes/experiment-red-analysis.json",
            # "red-grid": "./scenes/experiment-red-grid.json",
            "red-rh": "./scenes/experiment-red-rh.json",
        },
        match_settings={
            "experiment": "./scenes/experiment-settings.json",
        },
        n_matches=5,
        max_workers=1,
    )
    run_experiment_set(my_run)


def run_experiment_set(
    experiment_set: ExperimentSetConfig,
) -> None:

    experiments: list[ExperimentConfig] = [
        ExperimentConfig(
            name="-".join(name for name, _ in combination),
            gs=get_game_state(list(path for _, path in combination)),
            n_matches=experiment_set.n_matches,
            experiment_run_config=get_config(),
        )
        for combination in product(
            experiment_set.scene_configs.items(),
            experiment_set.blue_configs.items(),
            experiment_set.red_configs.items(),
            experiment_set.match_settings.items(),
        )
    ]
    run_experiments(
        experiments,
        max_workers=experiment_set.max_workers,
    )


def run_experiments(
    experiments: list[ExperimentConfig],
    max_workers: int,
) -> None:
    # Create a list of matches to work on
    matches: list[tuple[GameState, ExperimentConfig]] = []
    for experiment in experiments:
        current_tally = get_results(experiment)
        remaining_matches = max(0, experiment.n_matches - current_tally.n_matches)
        gs = deepcopy(experiment.gs)
        for _ in range(remaining_matches):
            matches.append((gs, experiment))

    # Randomize to run evenly across all matches
    random.shuffle(matches)

    # Run this in parallel
    pool_type: type[Pool] | type[ThreadPool] = ThreadPool
    with pool_type(processes=max_workers) as p:
        results = p.imap_unordered(run_match_cloud, matches)
        for match_result in results:
            result, experiment = match_result
            print(f"    {experiment.name} done, tallying")
            experiment_result = get_results(experiment)
            if experiment_result.n_matches == experiment.n_matches:
                continue
            match_results = experiment_result.match_results
            match_results.append(result)
            experiment_result.n_matches = len(match_results)
            save_results(experiment, experiment_result)


def run_match(
    match: tuple[GameState, ExperimentConfig],
) -> tuple[MatchResult, ExperimentConfig]:
    gs, experiment = match
    print(f"Running match {experiment.name}")
    result = AiMatch.run_match(gs)
    return (
        MatchResult(
            winner=result.winner,
            total_runtime=result.runtime,
            blue_search_sizes=result.blue_search_sizes,
            red_search_sizes=result.red_search_sizes,
        ),
        experiment,
    )


def run_match_cloud(
    match: tuple[GameState, ExperimentConfig],
) -> tuple[MatchResult, ExperimentConfig]:
    gs, experiment = match
    print(f"Running match {experiment.name}")

    scene_data = Serializer.serialize(
        entities=gs.dump(),
        component_types=list(get_component_types()),
    )

    r = requests.post(
        f"{experiment.experiment_run_config.url}/api/ai-play",
        data=scene_data,
    )
    if 300 <= r.status_code <= 600:
        raise Exception(f"Request had {r.status_code} error: {r.text}")
    response = AiMatchResponse(**r.json())

    return (
        MatchResult(
            winner=response.winner,
            total_runtime=response.total_runtime,
            blue_search_sizes=response.blue_search_sizes,
            red_search_sizes=response.red_search_sizes,
        ),
        experiment,
    )


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


def get_results(experiment: ExperimentConfig) -> ExperimentResult:
    file_path = f"{FOLDER}{experiment.name}.json"
    if not Path(file_path).is_file():
        blue_config: AiConfigComponent | None = None
        red_config: AiConfigComponent | None = None
        for _, config in experiment.gs.query(AiConfigComponent):
            if config.faction == InitiativeState.Faction.BLUE:
                blue_config = config
            if config.faction == InitiativeState.Faction.RED:
                red_config = config
        if blue_config == None:
            raise Exception("AI config is missing for BLUE.")
        if red_config == None:
            raise Exception("AI config is missing for RED.")

        return ExperimentResult(
            n_matches=0,
            blue_config=blue_config,
            red_config=red_config,
            match_results=[],
        )

    with open(file_path, "r") as f:
        # This file reading is unreliable... need better file IO?
        file_data = f.read()
        if file_data == "":
            raise Exception(f"{file_path} file fmpty?!")
        return ExperimentResult.model_validate_json(file_data)


def save_results(
    experiment: ExperimentConfig,
    result: ExperimentResult,
) -> None:
    file_path = f"{FOLDER}{experiment.name}.json"
    with open(file_path, "w") as f:
        f.write(result.model_dump_json(indent=2))


def get_config() -> ExperimentRunConfig:
    with open("./scripts/configs/experiment-config.json", "r") as f:
        return ExperimentRunConfig(**json.loads(f.read()))


if __name__ == "__main__":
    main()
