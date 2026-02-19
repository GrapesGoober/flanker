from copy import deepcopy

from flanker_ai.unabstracted.models import ActionResult
from flanker_ai.waypoints.waypoints_minimax_search import WaypointsMinimaxSearch
from flanker_ai.waypoints.waypoints_scheme import WaypointScheme
from flanker_core.gamestate import GameState
from flanker_core.models.components import InitiativeState
from flanker_core.models.outcomes import InvalidAction
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.objective_system import ObjectiveSystem


class WaypointsMinimaxAgent:
    """Provides agent instance for waypoints-minimax search to play the game."""

    def __init__(
        self,
        gs: GameState,
        faction: InitiativeState.Faction,
        search_depth: int,
        waypoint_coordinates: list[Vec2],
        path_tolerance: float,
        max_action_per_initiative: int = 20,
    ) -> None:
        self._gs = gs
        self._faction: InitiativeState.Faction = faction
        self._template_waypoints_gs = WaypointScheme.create_template_waypoints(
            gs,
            points=waypoint_coordinates,
            path_tolerance=path_tolerance,
        )
        self._path_tolerance = path_tolerance
        self._depth = search_depth
        self._MAX_ACTION_PER_INITIATIVE = max_action_per_initiative

    def play_initiative(self) -> list[ActionResult]:
        if InitiativeSystem.get_initiative(self._gs) != self._faction:
            return []

        self._template_waypoints_gs.initiative = self._faction
        halt_counter = 0
        action_results: list[ActionResult] = []
        # TODO: should this while loop be done away? Let caller manage it.
        while InitiativeSystem.get_initiative(self._gs) == self._faction:
            if ObjectiveSystem.get_winning_faction(self._gs) != None:
                break
            # Prepare the abstraction for searching
            new_waypoint_gs = WaypointScheme.update_template(
                self._template_waypoints_gs,
                self._gs,
                path_tolerance=self._path_tolerance,
            )
            # Check redundant moves (stop search)
            if halt_counter > self._MAX_ACTION_PER_INITIATIVE:
                print("AI made useless actions, breaking")
                InitiativeSystem.flip_initiative(self._gs)
                break
            # Runs the abstracted graph search
            _, waypoint_actions = WaypointsMinimaxSearch.search_best_actions(
                new_waypoint_gs,
                depth=self._depth,
            )

            if len(waypoint_actions) == 0:
                print("No valid action for AI, breaking")
                InitiativeSystem.flip_initiative(self._gs)
                break

            current_action = waypoint_actions[0]
            result = WaypointScheme.apply_action(
                gs=self._gs,
                waypoint_gs=new_waypoint_gs,
                waypoint_action=current_action,
            )
            if isinstance(result, InvalidAction):
                print("AI made invalid action, breaking")
                InitiativeSystem.flip_initiative(self._gs)
                break
            # These result objects would be used for logging
            # Thus, prevent mutation by creating a copy
            result = deepcopy(result)
            action_results.append(result)
            halt_counter += 1

        return action_results
