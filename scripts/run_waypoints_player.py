from dataclasses import is_dataclass
from inspect import isclass
from typing import Any

from flanker_ai.waypoints.waypoints_minimax_player import WaypointsMinimaxPlayer
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

waypoints_gs = WaypointScheme.create_grid_waypoints(gs, spacing=20, offset=10)
_, waypoint_actions = WaypointsMinimaxPlayer.play(waypoints_gs, depth=4)
print(waypoint_actions)
# exec_time = timeit(lambda: AiService.play_waypointsgraph_minimax(gs, depth=4), number=1)
# print(f"Execution time: {exec_time:.6f} seconds")
