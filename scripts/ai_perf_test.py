import random
from dataclasses import is_dataclass
from inspect import isclass
from typing import Any

from flanker_ai.ai_agent import AiAgent
from flanker_ai.ai_trial import AiTrial
from flanker_ai.components import AiConfigComponent, InitiativeState
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.serializer import Serializer
from flanker_core.systems.register_systems import register_systems


def load_state(path: str) -> GameState:

    component_types: list[type[Any]] = []
    for _, cls in vars(components).items():
        if isclass(cls) and is_dataclass(cls):
            component_types.append(cls)
    component_types.append(AiConfigComponent)

    with open(path, "r") as f:
        entities = Serializer.deserialize(
            json_data=f.read(),
            component_types=component_types,
        )
        gs = GameState.load(entities)

    register_systems(gs)
    return gs


if __name__ == "__main__":
    PATH = "./scenes/experiment-s2.json"
    gs = load_state(PATH)

    # Ensures that each run is consistent in search size
    random.seed(10)

    # Initialize the state first
    _ = AiAgent.get_agent(gs, InitiativeState.Faction.BLUE)
    _ = AiAgent.get_agent(gs, InitiativeState.Faction.RED)

    def run_ai_trial() -> None:
        result = AiTrial.run_trial(gs)
        if result.winner == None:
            print(f"No winner; draw")
        else:
            print(f"Winner is {result.winner}")

    # from timeit import timeit

    # exec_time = timeit(run_ai_trial, number=1)
    # print(f"Execution time: {exec_time:.6f} seconds")

    import cProfile
    import pstats

    cProfile.run("run_ai_trial()", sort="tottime", filename="./scripts/ai-perftest.txt")
    p = pstats.Stats("./scripts/ai-perftest.txt")
    p.sort_stats("tottime")
    p.print_stats(20)
