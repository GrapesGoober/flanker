from dataclasses import is_dataclass
from inspect import isclass
from typing import Any

from flanker_ai.components import InitiativeState
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.models.vec2 import Vec2
from flanker_core.serializer import Serializer
from flanker_core.systems.move_system import MoveSystem

component_types: list[type[Any]] = []
for _, cls in vars(components).items():
    if isclass(cls) and is_dataclass(cls):
        component_types.append(cls)

path = "./scenes/demo.json"

with open(path, "r") as f:
    entities = Serializer.deserialize(
        json_data=f.read(),
        component_types=component_types,
    )
    gs = GameState.load(entities)

# for id, unit in gs.query(components.CombatUnit):
#     if unit.faction == InitiativeState.Faction.RED:
#         continue
#     # Run one move action to precache
#     MoveSystem.move(gs, id, Vec2(-50, -200))
#     break


def move_many_times() -> None:

    for id, unit in gs.query(components.CombatUnit):
        if unit.faction == InitiativeState.Faction.RED:
            continue

        MoveSystem.move(gs, id, Vec2(-50, -200))


from timeit import timeit

exec_time = timeit(move_many_times, number=1)
print(f"Execution time: {exec_time:.6f} seconds")

# import cProfile
# import pstats

# cProfile.run("move_many_times()", sort="tottime", filename="perftest.txt")
# p = pstats.Stats("./scripts/perftest.txt")
# p.sort_stats("tottime")
# p.print_stats(20)
