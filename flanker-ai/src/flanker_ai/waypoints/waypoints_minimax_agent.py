from copy import deepcopy

from flanker_ai.policies.minimax_search import MinimaxSearch
from flanker_ai.unabstracted.models import ActionResult
from flanker_ai.waypoints.waypoints_converter import WaypointConverter
from flanker_core.gamestate import GameState
from flanker_core.models.components import InitiativeState
from flanker_core.models.outcomes import InvalidAction
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.objective_system import ObjectiveSystem

_MAX_ACTION_PER_INITIATIVE = 20


class WaypointsMinimaxAgent:
    """Provides agent instance for waypoints-minimax search to play the game."""

    def __init__(
        self,
        gs: GameState,
        faction: InitiativeState.Faction,
        search_depth: int,
        waypoint_coordinates: list[Vec2],
        path_tolerance: float,
    ) -> None:
        self._gs = gs
        self._faction: InitiativeState.Faction = faction
        self._template_waypoints_gs = WaypointConverter.create_template_state(
            gs,
            points=waypoint_coordinates,
            path_tolerance=path_tolerance,
        )
        self._path_tolerance = path_tolerance
        self._depth = search_depth

    def play_initiative(self) -> list[ActionResult]:
        if InitiativeSystem.get_initiative(self._gs) != self._faction:
            return []

        self._template_waypoints_gs.initiative = self._faction
        halt_counter = 0
        action_results: list[ActionResult] = []
        while InitiativeSystem.get_initiative(self._gs) == self._faction:
            if ObjectiveSystem.get_winning_faction(self._gs) != None:
                break
            # Add the combat units to the graph.
            # Make sure to add to a new graph instance to avoid mutation.
            new_waypoint_gs = deepcopy(self._template_waypoints_gs)
            WaypointConverter.add_combat_units(
                new_waypoint_gs,
                self._gs,
                path_tolerance=self._path_tolerance,
            )
            # Check redundant moves (stop search)
            if halt_counter > _MAX_ACTION_PER_INITIATIVE:
                print("AI made useless actions, breaking")
                InitiativeSystem.flip_initiative(self._gs)
                break
            # Runs the abstracted graph search
            _, waypoint_action = MinimaxSearch.search(
                state=new_waypoint_gs,
                depth=4,
            )

            if waypoint_action == None:
                print("No valid action for AI, breaking")
                InitiativeSystem.flip_initiative(self._gs)
                break

            result = WaypointConverter.apply_action(
                gs=self._gs,
                waypoint_gs=new_waypoint_gs,
                waypoint_action=waypoint_action,
            )
            if isinstance(result, InvalidAction):
                print("AI made invalid action, breaking")
                InitiativeSystem.flip_initiative(self._gs)
                break
            # These result objects would be used for logging
            # Thus, prevent mutation by creating a copy
            action_results.append(deepcopy(result))
            halt_counter += 1

        return action_results
