import random
from copy import deepcopy
from dataclasses import dataclass, is_dataclass
from inspect import isclass
from itertools import product
from multiprocessing.pool import Pool, ThreadPool
from pathlib import Path
from time import sleep
from typing import Any, Iterable, Literal
from uuid import UUID

import requests
from experiment_models import (
    ExperimentMetadata,
    ExperimentSetConfig,
    MatchResult,
)
from flanker_ai.ai_agent import AiAgent
from flanker_ai.ai_match import AiMatch
from flanker_ai.components import AiConfigComponent
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.models.components import InitiativeState
from flanker_core.serializer import Serializer
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


@dataclass
class _ExperimentConfig:
    """Input config model for running a many matches."""

    name: str
    gs: GameState
    n_matches: int
    target: Literal["local"] | str


@dataclass
class _MatchConfig:
    """Input config model for running a single match."""

    name: str
    gs: GameState
    n_matches: int
    target: Literal["local"] | str


class _MatchResultApiResponse(BaseModel):
    """Response model from WebAPI, kept separate from MatchResult."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    winner: InitiativeState.Faction | None
    total_runtime: float
    blue_search_sizes: list[int]
    red_search_sizes: list[int]


def main() -> None:
    results_root_path = "./scripts/outputs/experiment-results/"

    experiment_set = get_config(
        config_path="./scripts/configs/experiment-config.json",
    )
    experiments = get_experiments(experiment_set)

    for experiment in experiments:
        init_metadata_file(experiment, results_root_path)

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

    # Run and record all matches
    with pool_type(processes=experiment_set.max_workers) as p:
        results = p.imap_unordered(run_match, matches)
        for match_result in results:
            result, match_config = match_result
            print(f"    {match_config.name} done, tallying")
            experiment_metadata = get_metadata(
                experiment_name=match_config.name,
                results_root_path=results_root_path,
            )
            if experiment_metadata.n_matches == match_config.n_matches:
                continue
            experiment_metadata.n_matches += 1
            update_metadata(
                experiment_name=match_config.name,
                metadata=experiment_metadata,
                results_root_path=results_root_path,
            )
            append_results(
                experiment_name=match_config.name,
                result=result,
                results_root_path=results_root_path,
            )


def get_config(config_path: str) -> ExperimentSetConfig:
    with open(config_path, "r") as f:
        return ExperimentSetConfig.model_validate_json(f.read())


def run_match(
    match_config: _MatchConfig,
) -> tuple[MatchResult, _MatchConfig]:
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
            print(f"Request had {r.status_code} error: {r.text}")
            print(f"Rerunning {match_config.name} in 30 seconds")
            sleep(30)
            return run_match(match_config)

        result = _MatchResultApiResponse.model_validate_json(r.text)

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
) -> list[_ExperimentConfig]:
    return [
        _ExperimentConfig(
            name="-".join(name for name in combination),
            gs=get_game_state(
                [experiment_set.scene_files[name] for name in combination]
            ),
            n_matches=experiment_set.n_matches,
            target=experiment_set.target,
        )
        for combination in product(
            experiment_set.scene_configs,
            experiment_set.blue_configs,
            experiment_set.red_configs,
            experiment_set.match_settings,
        )
    ]


def get_matches(
    experiments: list[_ExperimentConfig],
    results_root_path: str,
) -> list[_MatchConfig]:
    matches: list[_MatchConfig] = []
    for experiment in experiments:
        current_tally = get_metadata(
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
                _MatchConfig(
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


def init_metadata_file(
    experiment_config: _ExperimentConfig,
    results_root_path: str,
) -> None:
    file_path = Path(results_root_path) / f"{experiment_config.name}-metadata.json"

    # If data already exists, avoid rerunning (need a manual file delete)
    if Path(file_path).is_file():
        return

    # Record AI configs as metadata
    blue_config: AiConfigComponent | None = None
    red_config: AiConfigComponent | None = None
    for _, ai_config in experiment_config.gs.query(AiConfigComponent):
        match ai_config.faction:
            case InitiativeState.Faction.BLUE:
                blue_config = ai_config
            case InitiativeState.Faction.RED:
                red_config = ai_config
    if blue_config == None or red_config == None:
        raise Exception(f"AI configs missing!")

    # Save file
    with open(file_path, "w") as f:
        f.write(
            ExperimentMetadata(
                n_matches=0,
                blue_config=blue_config,
                red_config=red_config,
            ).model_dump_json(indent=2)
        )


def get_metadata(
    experiment_name: str,
    results_root_path: str,
) -> ExperimentMetadata:
    file_path = Path(results_root_path) / f"{experiment_name}-metadata.json"
    if not Path(file_path).is_file():
        raise Exception(f"Metadata file for {experiment_name} does not exist")

    with open(file_path, "r") as f:
        file_data = f.read()
        if file_data == "":
            raise Exception(f"{file_path} file empty?!")
        return ExperimentMetadata.model_validate_json(file_data)


def update_metadata(
    experiment_name: str,
    metadata: ExperimentMetadata,
    results_root_path: str,
) -> None:
    file_path = Path(results_root_path) / f"{experiment_name}-metadata.json"
    if not Path(file_path).is_file():
        raise Exception(f"Metadata file for {experiment_name} does not exist")

    # Save file
    with open(file_path, "w") as f:
        f.write(metadata.model_dump_json(indent=2))


def append_results(
    experiment_name: str,
    result: MatchResult,
    results_root_path: str,
) -> None:
    file_path = Path(results_root_path) / f"{experiment_name}.jsonl"
    with open(file_path, "a") as f:
        f.write(result.model_dump_json())
        f.write("\n")


if __name__ == "__main__":
    main()
