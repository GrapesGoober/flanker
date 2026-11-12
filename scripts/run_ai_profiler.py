import random
from dataclasses import is_dataclass
from inspect import isclass
from typing import Any, Iterable
from uuid import UUID

from flanker_ai.ai_system import AiSystem
from flanker_ai.config_models import AiConfigComponent
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.serializer import Serializer
from flanker_core.systems.action_system import ActionSystem
from match_experiments.experiment_models import SceneManifest


def get_component_types() -> Iterable[type]:
    for _, cls in vars(components).items():
        if isclass(cls) and is_dataclass(cls):
            yield cls
    yield AiConfigComponent


def get_game_state(
    scene_names: list[str],
) -> GameState:
    component_types = list(get_component_types())
    entities: dict[UUID, Any] = {}

    with open("./scenes/manifest.json", "r") as f:
        manifest = SceneManifest.model_validate_json(f.read())

    paths = [manifest.scene_paths[name] for name in scene_names]

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
        scene_names=[
            "experiment-settings",
            "scene-v2-1",
            "blue-grid-75-r1-expectimax",
            "red-rh",
        ]
    )

    # Ensures that each run is consistent in search size
    random.seed(10)

    def run_perf_test() -> None:
        # result = AiMatch.run_match(gs)
        # if result.winner == None:
        #     print(f"No winner; draw")
        # else:
        #     print(f"Winner is {result.winner}")
        initiative = ActionSystem.get_initiative(gs)
        AiSystem.perform_action(gs, faction=initiative)

    # from timeit import timeit

    # exec_time = timeit(run_perf_test, number=1)
    # print(f"Execution time: {exec_time:.6f} seconds")

    import cProfile
    import pstats

    prof_file = "./scripts/outputs/ai-perftest.prof"
    cProfile.run("run_perf_test()", sort="cumtime", filename=prof_file)
    p = pstats.Stats(prof_file)
    p.strip_dirs()
    p.sort_stats("cumtime")
    p.print_stats(20)
