from copy import deepcopy
from typing import Callable

from flanker_ai.unabstracted.models import ActionResult
from flanker_ai.waypoints.waypoints_minimax_search import WaypointsMinimaxSearch
from flanker_ai.waypoints.waypoints_scheme import WaypointScheme
from flanker_core.gamestate import GameState
from flanker_core.models.components import InitiativeState
from flanker_core.models.outcomes import InvalidAction
from flanker_core.systems.initiative_system import InitiativeSystem


class WaypointsMinimaxPlayer:
    def __init__(
        self,
        gs: GameState,
        faction: InitiativeState.Faction,
        search_depth: int,
        grid_spacing: float,
        grid_offset: float,
        max_action_per_initiative: int = 20,
    ) -> None:
        self._gs = gs
        self._faction: InitiativeState.Faction = faction
        self._waypoints_gs = WaypointScheme.create_grid_waypoints(
            gs,
            spacing=grid_spacing,
            offset=grid_offset,
        )
        self._grid_spacing = grid_spacing
        self._depth = search_depth
        self._MAX_ACTION_PER_INITIATIVE = max_action_per_initiative

    def play_initiative(
        self,
        action_callback: Callable[[ActionResult], None] | None = None,
    ) -> list[ActionResult]:
        if InitiativeSystem.get_initiative(self._gs) != self._faction:
            return []

        self._waypoints_gs.initiative = self._faction
        halt_counter = 0
        action_results: list[ActionResult] = []
        while InitiativeSystem.get_initiative(self._gs) == self._faction:
            # Prepare the abstraction for searching
            new_waypoint_gs = deepcopy(self._waypoints_gs)
            WaypointScheme.add_combat_units(
                new_waypoint_gs,
                self._gs,
                path_tolerance=self._grid_spacing / 2,
            )
            # Check redundant moves (stop search)
            if halt_counter > self._MAX_ACTION_PER_INITIATIVE:
                InitiativeSystem.flip_initiative(self._gs)
                print("AI made useless actions, breaking")
                break
            # Runs the abstracted graph search
            _, waypoint_actions = WaypointsMinimaxSearch.play(
                new_waypoint_gs,
                depth=self._depth,
            )
            if len(waypoint_actions) == 0:
                print("No valid action for AI, breaking")

            current_action = waypoint_actions[0]
            result = WaypointScheme.apply_action(
                gs=self._gs,
                waypoint_gs=new_waypoint_gs,
                waypoint_action=current_action,
            )
            if isinstance(result, InvalidAction):
                InitiativeSystem.flip_initiative(self._gs)
                print("AI made invalid action, breaking")
                break

            action_results.append(result)
            halt_counter += 1
            if action_callback:
                action_callback(result)
        return action_results
