from copy import deepcopy
from dataclasses import is_dataclass
from inspect import isclass
from typing import Any

from flanker_ai.waypoints.waypoints_minimax_player import WaypointsMinimaxPlayer
from flanker_ai.waypoints.waypoints_scheme import WaypointScheme
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.models.components import InitiativeState
from flanker_core.models.outcomes import InvalidAction
from flanker_core.serializer import Serializer
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.objective_system import ObjectiveSystem

MAX_ACTION_PER_INITIATIVE = 20
GRID_SPACING = 20


class MinimaxGridPlayer:
    def __init__(
        self, gs: GameState, faction: InitiativeState.Faction, search_depth: int
    ) -> None:
        self._gs = gs
        self._faction: InitiativeState.Faction = faction
        self._waypoints_gs = WaypointScheme.create_grid_waypoints(
            gs,
            spacing=GRID_SPACING,
            offset=GRID_SPACING / 2,
        )
        self._depth = search_depth

    def play_if_has_initiative(self) -> None:
        if InitiativeSystem.get_initiative(self._gs) != self._faction:
            return

        halt_counter = 0
        while InitiativeSystem.get_initiative(self._gs) == self._faction:
            new_gs = deepcopy(self._waypoints_gs)
            WaypointScheme.add_combat_units(
                new_gs,
                gs,
                path_tolerance=GRID_SPACING,
            )
            if halt_counter > MAX_ACTION_PER_INITIATIVE:
                InitiativeSystem.flip_initiative(self._gs)
                print("AI made useless actions, breaking")
            # Runs the abstracted graph search
            _, waypoint_actions = WaypointsMinimaxPlayer.play(new_gs, depth=self._depth)
            if len(waypoint_actions) == 0:
                print("No valid action for AI, breaking")

            current_action = waypoint_actions[0]
            result = WaypointScheme.apply_action(self._gs, new_gs, current_action)
            if isinstance(result, InvalidAction):
                InitiativeSystem.flip_initiative(self._gs)
                print("AI made invalid action, breaking")
            halt_counter += 1


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
    red_player = MinimaxGridPlayer(
        gs,
        InitiativeState.Faction.RED,
        search_depth=4,
    )
    print("Creating BLUE player...")
    blue_player = MinimaxGridPlayer(
        gs,
        InitiativeState.Faction.BLUE,
        search_depth=4,
    )

    print("Running...")
    while ObjectiveSystem.get_winning_faction(gs) == None:
        red_player.play_if_has_initiative()
        blue_player.play_if_has_initiative()

    print(f"Winner is {ObjectiveSystem.get_winning_faction(gs)}")
