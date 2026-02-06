from dataclasses import is_dataclass
from inspect import isclass
from typing import Any

from flanker_ai.waypoints.waypoints_minimax_player import WaypointsMinimaxPlayer
from flanker_ai.waypoints.waypoints_scheme import ActionResult
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.models.components import InitiativeState
from flanker_core.serializer import Serializer
from flanker_core.systems.objective_system import ObjectiveSystem

MAX_ACTION_PER_INITIATIVE = 20
GRID_SPACING = 20


def load_game(path: str) -> GameState:
    component_types: list[type[Any]] = []
    for _, cls in vars(components).items():
        if isclass(cls) and is_dataclass(cls):
            component_types.append(cls)

    with open(path, "r") as f:
        entities, id_counter = Serializer.deserialize(
            json_data=f.read(),
            component_types=component_types,
        )
        return GameState.load(entities, id_counter)


if __name__ == "__main__":
    gs = load_game(path="./scenes/demo-simple-stochastic.json")
    print("Creating RED player...")
    red_player = WaypointsMinimaxPlayer(
        gs,
        InitiativeState.Faction.RED,
        search_depth=4,
        grid_spacing=20,
        grid_offset=10,
    )
    print("Creating BLUE player...")
    blue_player = WaypointsMinimaxPlayer(
        gs,
        InitiativeState.Faction.BLUE,
        search_depth=4,
        grid_spacing=20,
        grid_offset=10,
    )

    def print_result_red(result: ActionResult) -> None:
        print(f"RED made action {result}")

    def print_result_blue(result: ActionResult) -> None:
        print(f"BLUE made action {result}")

    while ObjectiveSystem.get_winning_faction(gs) == None:
        red_player.play_initiative(action_callback=print_result_red)
        blue_player.play_initiative(action_callback=print_result_blue)

    print(f"Winner is {ObjectiveSystem.get_winning_faction(gs)}")
