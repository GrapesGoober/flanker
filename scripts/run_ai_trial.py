from copy import deepcopy
from dataclasses import is_dataclass
from inspect import isclass
from pathlib import Path
from typing import Any

from flanker_ai.ai_agent import AiAgent, AiConfigComponent
from flanker_ai.ai_trial import AiTrial
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.models.components import InitiativeState
from flanker_core.serializer import Serializer
from flanker_core.systems.register_systems import register_systems
from pydantic import BaseModel


def initialize_game_state(path: str) -> GameState:
    component_types: list[type[Any]] = []
    component_types.append(AiConfigComponent)
    for _, cls in vars(components).items():
        if isclass(cls) and is_dataclass(cls):
            component_types.append(cls)

    with open(path, "r") as f:
        entities = Serializer.deserialize(
            json_data=f.read(),
            component_types=component_types,
        )
        gs = GameState.load(entities)
    register_systems(gs)
    print("Creating BLUE agent...")
    AiAgent.get_agent(gs, InitiativeState.Faction.BLUE)
    print("Creating RED agent...")
    AiAgent.get_agent(gs, InitiativeState.Faction.RED)
    return gs


class BatchTally(BaseModel):
    trials: int
    blue_wins: int
    red_wins: int
    draws: int
    blue_config: AiConfigComponent
    red_config: AiConfigComponent


def get_current_tally(record_file: str) -> BatchTally:
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

        return BatchTally(
            trials=0,
            blue_wins=0,
            red_wins=0,
            draws=0,
            blue_config=blue_config,
            red_config=red_config,
        )

    with open(record_file, "r") as f:
        return BatchTally.model_validate_json(f.read())


def save_tally(record_file: str, tally: BatchTally) -> None:
    with open(record_file, "w") as f:
        f.write(tally.model_dump_json(indent=2))


def run_trial(
    gs: GameState,
    record_file: str,
    n: int = 1,
) -> None:

    # Initialize the file if not exist
    tally = get_current_tally(record_file)
    save_tally(record_file, tally)

    while tally.trials < n:
        print(f"Running new trial")
        new_gs = deepcopy(gs)
        result = AiTrial.run_trial(new_gs)
        tally = get_current_tally(record_file)  # Resync a new tally
        tally.trials += 1
        if tally.trials > n:
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
    SCENE_NAME = "experiment-2-grid"
    SCENE_FILE = f"./scenes/{SCENE_NAME}.json"
    RECORD_FILE = f"./scripts/experiment_results/{SCENE_NAME}.json"
    gs = initialize_game_state(path=SCENE_FILE)
    run_trial(gs, RECORD_FILE, n=100)
