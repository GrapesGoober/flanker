import random
from dataclasses import is_dataclass
from inspect import isclass
from itertools import product
from multiprocessing.pool import Pool
from pathlib import Path
from time import sleep
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


class ExperimentConfig(BaseModel):
    n_matches: int
    scenes: list[str]


class ExperimentSetConfig(BaseModel):
    scene_configs: list[str]
    blue_config: list[str]
    red_config: list[str]
    settings_config: list[str]
    n_matches: int
    max_processes: int


def main() -> None:
    my_run = ExperimentSetConfig(
        scene_configs=[
            "experiment-scene-1",
            "experiment-scene-2",
        ],
        blue_config=[
            "experiment-blue-analysis",
            "experiment-blue-grid",
            "experiment-blue-rh",
        ],
        red_config=[
            "experiment-red-analysis",
            "experiment-red-grid",
            "experiment-red-rh",
        ],
        settings_config=[
            "experiment-settings",
        ],
        n_matches=20,
        max_processes=5,
    )
    run_experiment_set(my_run)


def run_experiment_set(
    experiment_set: ExperimentSetConfig,
) -> None:

    experiments: list[ExperimentConfig] = [
        ExperimentConfig(
            scenes=list(combination),
            n_matches=experiment_set.n_matches,
        )
        for combination in product(
            experiment_set.scene_configs,
            experiment_set.blue_config,
            experiment_set.red_config,
            experiment_set.settings_config,
        )
    ]
    run_experiments(
        experiments,
        max_processes=experiment_set.max_processes,
    )


def run_experiments(
    experiments: list[ExperimentConfig],
    max_processes: int,
) -> None:

    game_states: dict[str, GameState] = {
        str(experiment.scenes): get_game_state(experiment.scenes)
        for experiment in experiments
    }

    # Create a list of matches to work on
    matches: list[tuple[GameState, ExperimentConfig]] = []
    for experiment in experiments:
        gs = game_states[str(experiment.scenes)]
        current_tally = get_tally(gs, experiment)
        remaining_matches = max(0, experiment.n_matches - current_tally.n_matches)
        for _ in range(remaining_matches):
            matches.append((game_states[str(experiment.scenes)], experiment))

    # Randomize to run evenly across all matches
    random.shuffle(matches)

    # Run this in parallel
    with Pool(processes=max_processes) as p:
        results = p.imap_unordered(run_match, matches)
        for match_result in results:
            result, experiment = match_result
            print(f"    {experiment.scenes} done, tallying")
            gs = game_states[str(experiment.scenes)]
            tally = get_tally(gs, experiment)
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
    print(f"Running experiment {experiment.scenes}")
    result = AiMatch.run_match(gs)
    sleep(0.1)
    return result, experiment


def get_game_state(
    scenes: list[str],
) -> GameState:
    component_types: list[type[Any]] = []
    component_types.append(AiConfigComponent)
    for _, cls in vars(components).items():
        if isclass(cls) and is_dataclass(cls):
            component_types.append(cls)

    entities: dict[UUID, Any] = {}
    paths = [f"./scenes/{scene}.json" for scene in scenes]
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


def get_tally(gs: GameState, experiment: ExperimentConfig) -> ExperimentTally:
    file_name = "-".join(experiment.scenes)
    file_path = f"./scripts/experiment_results/{file_name}.json"
    if not Path(file_path).is_file():
        blue_config: AiConfigComponent | None = None
        red_config: AiConfigComponent | None = None
        for _, config in gs.query(AiConfigComponent):
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
    file_name = "-".join(experiment.scenes)
    file_path = f"./scripts/experiment_results/{file_name}.json"
    with open(file_path, "w") as f:
        f.write(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
