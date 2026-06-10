from dataclasses import is_dataclass
from inspect import isclass
from typing import Any

from flanker_ai.components import InitiativeState
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.serializer import Serializer
from flanker_core.systems.los_system import LosSystem
from flanker_core.systems.register_systems import register_systems


def load_state(path: str) -> GameState:

    component_types: list[type[Any]] = []
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
    return gs


if __name__ == "__main__":
    PATH = "./scenes/demo.json"
    gs = load_state(PATH)

    los_system = gs.get(LosSystem)

    def calculate_visibility() -> None:

        for _, unit, transform in gs.query(
            components.CombatUnit,
            components.Transform,
        ):
            if unit.faction == InitiativeState.Faction.RED:
                continue

            los_system.get_los_polygon(gs, transform.position)

    from timeit import timeit

    exec_time = timeit(calculate_visibility, number=1)
    print(f"Execution time: {exec_time:.6f} seconds")

    # import cProfile
    # import pstats

    # cProfile.run("move_many_times()", sort="tottime", filename="perftest.txt")
    # p = pstats.Stats("./scripts/perftest.txt")
    # p.sort_stats("tottime")
    # p.print_stats(20)
