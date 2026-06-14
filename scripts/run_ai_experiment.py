from copy import deepcopy
from dataclasses import is_dataclass
from inspect import isclass
from pathlib import Path
from typing import Any
from uuid import UUID

from flanker_ai.ai_agent import AiAgent, AiConfigComponent
from flanker_ai.ai_match import AiMatch
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.models.components import InitiativeState
from flanker_core.serializer import Serializer
from flanker_core.systems.register_systems import register_systems
from pydantic import BaseModel


class ExperimentResults(BaseModel):
    n_matches: int
    blue_wins: int
    red_wins: int
    draws: int
    blue_config: AiConfigComponent
    red_config: AiConfigComponent


class ExperimentConfig(BaseModel):
    n_matches: int
    scenes: list[str]


def initialize_game_state(
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
    print("Creating BLUE agent...")
    AiAgent.get_agent(gs, InitiativeState.Faction.BLUE)
    print("Creating RED agent...")
    AiAgent.get_agent(gs, InitiativeState.Faction.RED)
    return gs


def get_current_result(
    gs: GameState,
    record_file: str,
) -> ExperimentResults:
    if not Path(record_file).is_file():
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

        return ExperimentResults(
            n_matches=0,
            blue_wins=0,
            red_wins=0,
            draws=0,
            blue_config=blue_config,
            red_config=red_config,
        )

    with open(record_file, "r") as f:
        return ExperimentResults.model_validate_json(f.read())


def save_result(
    record_file: str,
    result: ExperimentResults,
) -> None:
    with open(record_file, "w") as f:
        f.write(result.model_dump_json(indent=2))


def run_experiment(
    experiment: ExperimentConfig,
) -> None:

    paths = [f"./scenes/{scene}.json" for scene in experiment.scenes]
    gs = initialize_game_state(paths=paths)

    experiment_name = "-".join(experiment.scenes)
    record_file = f"./scripts/experiment_results/{experiment_name}.json"

    # Initialize the file if not exist
    tally = get_current_result(gs, record_file)
    save_result(record_file, tally)

    while tally.n_matches < experiment.n_matches:
        print(f"Running new match")
        new_gs = deepcopy(gs)
        result = AiMatch.run_match(new_gs)
        tally = get_current_result(gs, record_file)  # Resync a new tally
        tally.n_matches += 1
        if tally.n_matches > experiment.n_matches:
            break
        match result.winner:
            case None:
                tally.draws += 1
            case InitiativeState.Faction.BLUE:
                tally.blue_wins += 1
            case InitiativeState.Faction.RED:
                tally.red_wins += 1
        save_result(record_file, tally)
        print(f"Match {tally.n_matches} finished with winner {result.winner}")


# Started 09:35, 8(x2) processes, 100% CPU, finished 10:20
if __name__ == "__main__":
    conf = ExperimentConfig(
        n_matches=100,
        scenes=["experiment-2-grid"],
    )
    run_experiment(conf)
