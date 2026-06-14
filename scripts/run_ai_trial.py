from copy import deepcopy
from dataclasses import is_dataclass
from inspect import isclass
from pathlib import Path
from typing import Any
from uuid import UUID

from flanker_ai.ai_agent import AiAgent, AiConfigComponent
from flanker_ai.ai_trial import AiTrial
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.models.components import InitiativeState
from flanker_core.serializer import Serializer
from flanker_core.systems.register_systems import register_systems
from pydantic import BaseModel


class BatchResults(BaseModel):
    trials: int
    blue_wins: int
    red_wins: int
    draws: int
    blue_config: AiConfigComponent
    red_config: AiConfigComponent


class BatchConfig(BaseModel):
    trials: int
    scenes: list[str]


def initialize_game_state(paths: list[str]) -> GameState:
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


def get_current_tally(
    gs: GameState,
    record_file: str,
) -> BatchResults:
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

        return BatchResults(
            trials=0,
            blue_wins=0,
            red_wins=0,
            draws=0,
            blue_config=blue_config,
            red_config=red_config,
        )

    with open(record_file, "r") as f:
        return BatchResults.model_validate_json(f.read())


def save_tally(
    record_file: str,
    tally: BatchResults,
) -> None:
    with open(record_file, "w") as f:
        f.write(tally.model_dump_json(indent=2))


def run_batch(
    batch: BatchConfig,
) -> None:

    paths = [f"./scenes/{scene}.json" for scene in batch.scenes]
    gs = initialize_game_state(paths=paths)

    batch_name = "-".join(batch.scenes)
    record_file = f"./scripts/experiment_results/{batch_name}.json"

    # Initialize the file if not exist
    tally = get_current_tally(gs, record_file)
    save_tally(record_file, tally)

    while tally.trials < batch.trials:
        print(f"Running new trial")
        new_gs = deepcopy(gs)
        result = AiTrial.run_trial(new_gs)
        tally = get_current_tally(gs, record_file)  # Resync a new tally
        tally.trials += 1
        if tally.trials > batch.trials:
            break
        match result.winner:
            case None:
                tally.draws += 1
            case InitiativeState.Faction.BLUE:
                tally.blue_wins += 1
            case InitiativeState.Faction.RED:
                tally.red_wins += 1
        save_tally(record_file, tally)
        print(f"Trial {tally.trials} finished with winner {result.winner}")


# Started 09:35, 8(x2) processes, 100% CPU, finished 10:20
if __name__ == "__main__":
    conf = BatchConfig(
        trials=100,
        scenes=["experiment-2-grid"],
    )
    run_batch(conf)
