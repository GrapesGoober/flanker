import csv
from copy import deepcopy
from dataclasses import is_dataclass
from inspect import isclass
from typing import Any

from flanker_ai.ai_agent import AiAgent, AiConfigComponent
from flanker_ai.ai_trial import AiTrial
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.models.components import InitiativeState
from flanker_core.serializer import Serializer


def initialize_game_state(path: str) -> GameState:
    component_types: list[type[Any]] = []
    component_types.append(AiConfigComponent)
    for _, cls in vars(components).items():
        if isclass(cls) and is_dataclass(cls):
            component_types.append(cls)

    with open(path, "r") as f:
        entities, id_counter = Serializer.deserialize(
            json_data=f.read(),
            component_types=component_types,
        )
        gs = GameState.load(entities, id_counter)

    print("Creating BLUE agent...")
    AiAgent.get_agent(gs, InitiativeState.Faction.BLUE)
    print("Creating RED agent...")
    AiAgent.get_agent(gs, InitiativeState.Faction.RED)
    return gs


def run_trial(
    gs: GameState,
    record_file: str,
    n: int = 1,
) -> None:
    with open(record_file, mode="w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["trial", "winner"])

    for i in range(n):
        print(f"Running Trial {i=}...")
        new_gs = deepcopy(gs)
        result = AiTrial.run_trial(new_gs)
        with open(record_file, mode="a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            if result.winner == None:
                writer.writerow([i, "DRAW"])
            else:
                print(f"Winner is {result.winner}")
                writer.writerow([i, result.winner.value])


if __name__ == "__main__":
    SCENE_NAME = "experiment-w1"
    SCENE_FILE = f"./scenes/{SCENE_NAME}.json"
    RECORD_FILE = f"./scripts/experiment_results/{SCENE_NAME}.csv"
    gs = initialize_game_state(path=SCENE_FILE)
    run_trial(gs, RECORD_FILE, n=300)
