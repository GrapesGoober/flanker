from dataclasses import is_dataclass
from inspect import isclass
from timeit import timeit
from typing import Any

from flanker_ai.waypoints.models import WaypointAction, WaypointsGraphGameState
from flanker_ai.waypoints.waypoints_minimax_search import WaypointsMinimaxSearch
from flanker_ai.waypoints.waypoints_scheme import WaypointScheme
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.serializer import Serializer

component_types: list[type[Any]] = []
for _, cls in vars(components).items():
    if isclass(cls) and is_dataclass(cls):
        component_types.append(cls)

path = "./scenes/demo-simple.json"

with open(path, "r") as f:
    entities, id_counter = Serializer.deserialize(
        json_data=f.read(),
        component_types=component_types,
    )
    gs = GameState.load(entities, id_counter)

waypoints_gs: WaypointsGraphGameState | None = None
waypoint_actions: list[WaypointAction] | None = None


def run_abstraction() -> None:
    global waypoints_gs
    waypoints_gs = WaypointScheme.create_template_waypoints(
        gs=gs,
        points=WaypointScheme.get_grid_coordinates(gs, 20, 10),
        path_tolerance=10,
    )


def run_search() -> None:
    assert waypoints_gs
    global waypoint_actions
    WaypointScheme.update_template(waypoints_gs, gs, path_tolerance=10)
    _, waypoint_actions = WaypointsMinimaxSearch.search_best_actions(
        waypoints_gs, depth=4
    )


print("abstracting...")
abstraction_time = timeit(run_abstraction, number=1)
print("done, adding combat units and searching...")
searching_time = timeit(run_search, number=1)
print(waypoint_actions)

print(f"Abstraction time: {abstraction_time:.6f} seconds")
print(f"Search time: {searching_time:.6f} seconds")
print(f"Total time: {searching_time+abstraction_time:.6f} seconds")
