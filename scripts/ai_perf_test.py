import random
from dataclasses import is_dataclass
from inspect import isclass
from typing import Any
from uuid import UUID

from flanker_ai.ai_agent import AiAgent
from flanker_ai.ai_match import AiMatch
from flanker_ai.components import AiConfigComponent
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.models.components import InitiativeState
from flanker_core.serializer import Serializer


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
    return gs


if __name__ == "__main__":
    gs = get_game_state(
        paths=[
            "./scenes/experiment-settings.json",
            "./scenes/experiment-scene-2.json",
            "./scenes/experiment-blue-analysis-weak.json",
            "./scenes/experiment-red-rh.json",
        ]
    )

    # Ensures that each run is consistent in search size
    random.seed(10)

    # Initialize the state first
    _ = AiAgent.get_agent(gs, InitiativeState.Faction.BLUE)
    _ = AiAgent.get_agent(gs, InitiativeState.Faction.RED)

    def run_ai_trial() -> None:
        result = AiMatch.run_match(gs)
        if result.winner == None:
            print(f"No winner; draw")
        else:
            print(f"Winner is {result.winner}")

    # from timeit import timeit

    # exec_time = timeit(run_ai_trial, number=1)
    # print(f"Execution time: {exec_time:.6f} seconds")

    import cProfile
    import pstats

    prof_file = "./scripts/ai-perftest.prof"
    cProfile.run("run_ai_trial()", sort="cumtime", filename=prof_file)
    p = pstats.Stats("./scripts/ai-perftest.prof")
    p.sort_stats("cumtime")
    p.print_stats(20)
