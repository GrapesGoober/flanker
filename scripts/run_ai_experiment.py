import random
from copy import deepcopy
from dataclasses import dataclass, is_dataclass
from inspect import isclass
from itertools import product
from multiprocessing.pool import Pool
from pathlib import Path
from typing import Any
from uuid import UUID

from flanker_ai.ai_agent import AiAgent, AiConfigComponent
from flanker_ai.ai_match import AiMatch, AiMatchResult
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.models.components import InitiativeState
from flanker_core.serializer import Serializer
from flanker_core.systems.register_systems import register_systems
from pydantic import BaseModel


class ExperimentTally(BaseModel):
    n_matches: int
    blue_wins: int
    red_wins: int
    draws: int
    blue_config: AiConfigComponent
    red_config: AiConfigComponent


@dataclass
class ExperimentConfig:
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
    max_processes: int


def main() -> None:
    my_run = ExperimentSetConfig(
        scene_configs={
            "scene-1": "./scenes/experiment-scene-1.json",
            "scene-2": "./scenes/experiment-scene-2.json",
        },
        blue_configs={
            "blue-analysis": "./scenes/experiment-blue-analysis.json",
            "blue-gridweak": "./scenes/experiment-blue-grid-weak.json",
            "blue-gridstrong": "./scenes/experiment-blue-grid-strong.json",
            "blue-rh": "./scenes/experiment-blue-rh.json",
        },
        red_configs={
            "red-analysis": "./scenes/experiment-red-analysis.json",
            "red-gridweak": "./scenes/experiment-red-grid-weak.json",
            "red-gridstrong": "./scenes/experiment-red-grid-strong.json",
            "red-rh": "./scenes/experiment-red-rh.json",
        },
        match_settings={
            "experiment": "./scenes/experiment-settings.json",
        },
        n_matches=100,
        max_processes=14,
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
        n_processes=experiment_set.max_processes,
    )


def run_experiments(
    experiments: list[ExperimentConfig],
    n_processes: int,
) -> None:
    # Create a list of matches to work on
    matches: list[tuple[GameState, ExperimentConfig]] = []
    for experiment in experiments:
        current_tally = get_tally(experiment)
        remaining_matches = max(0, experiment.n_matches - current_tally.n_matches)
        gs = deepcopy(experiment.gs)
        for _ in range(remaining_matches):
            matches.append((gs, experiment))

    # Randomize to run evenly across all matches
    random.shuffle(matches)

    # Run this in parallel
    with Pool(processes=n_processes) as p:
        results = p.imap_unordered(run_match, matches)
        for match_result in results:
            result, experiment = match_result
            print(f"    {experiment.name} done, tallying")
            tally = get_tally(experiment)
            if tally.n_matches == experiment.n_matches:
                continue
            tally.n_matches += 1
            match result.winner:
                case None:
                    tally.draws += 1
                case InitiativeState.Faction.BLUE:
                    tally.blue_wins += 1
                case InitiativeState.Faction.RED:
                    tally.red_wins += 1
            save_tally(experiment, tally)


def run_match(
    match: tuple[GameState, ExperimentConfig],
) -> tuple[AiMatchResult, ExperimentConfig]:
    gs, experiment = match
    print(f"Running match {experiment.name}")
    result = AiMatch.run_match(gs)
    return result, experiment


def get_game_state(
    paths: list[str],
) -> GameState:
    component_types: list[type[Any]] = []
    component_types.append(AiConfigComponent)
    for _, cls in vars(components).items():
        if isclass(cls) and is_dataclass(cls):
            component_types.append(cls)

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
    register_systems(gs)
    AiAgent.get_agent(gs, InitiativeState.Faction.BLUE)
    AiAgent.get_agent(gs, InitiativeState.Faction.RED)
    return gs


def get_tally(experiment: ExperimentConfig) -> ExperimentTally:
    file_path = f"./scripts/experiment_results/{experiment.name}.json"
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

        return ExperimentTally(
            n_matches=0,
            blue_wins=0,
            red_wins=0,
            draws=0,
            blue_config=blue_config,
            red_config=red_config,
        )

    with open(file_path, "r") as f:
        return ExperimentTally.model_validate_json(f.read())


def save_tally(
    experiment: ExperimentConfig,
    result: ExperimentTally,
) -> None:
    file_path = f"./scripts/experiment_results/{experiment.name}.json"
    with open(file_path, "w") as f:
        f.write(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
