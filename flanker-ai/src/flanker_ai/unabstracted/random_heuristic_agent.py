import random
from copy import deepcopy

from flanker_ai.unabstracted.models import (
    ActionResult,
    FireAction,
    FireActionResult,
    MoveAction,
    MoveActionResult,
)
from flanker_core.gamestate import GameState
from flanker_core.models.components import CombatUnit, InitiativeState, Transform
from flanker_core.models.outcomes import InvalidAction
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.command_system import ObjectiveSystem
from flanker_core.systems.fire_system import FireSystem
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.move_system import MoveSystem

_MAX_ACTION_PER_INITIATIVE = 20


class RandomHeuristicAgent:
    """
    Random Heuristic baseline agent.
    Logic:
    1. If an enemy is in LOF, Fire.
    2. Else, move a random distance along a vector towards the nearest enemy.
    """

    def __init__(
        self,
        faction: InitiativeState.Faction,
        gs: GameState,
    ) -> None:
        self._faction = faction
        self._gs = gs

    def play_initiative(self) -> list[ActionResult]:
        if InitiativeSystem.get_initiative(self._gs) != self._faction:
            return []

        halt_counter = 0
        action_results: list[ActionResult] = []
        # TODO: should this while loop be done away? Let caller manage it.
        while InitiativeSystem.get_initiative(self._gs) == self._faction:
            if ObjectiveSystem.get_winning_faction(self._gs) != None:
                break
            # Check redundant moves (stop search)
            if halt_counter > _MAX_ACTION_PER_INITIATIVE:
                print("AI made useless actions, breaking")
                InitiativeSystem.flip_initiative(self._gs)
                break

            action_result = self._perform_action()

            if action_result == None:
                print("No valid action for AI, breaking")
                InitiativeSystem.flip_initiative(self._gs)
                break

            if isinstance(action_result, InvalidAction):
                print("AI made invalid action, breaking")
                InitiativeSystem.flip_initiative(self._gs)
                break
            # These result objects would be used for logging
            # Thus, prevent mutation by creating a copy
            action_results.append(deepcopy(action_result))
            halt_counter += 1

        return action_results

    def _perform_action(self) -> ActionResult | None:
        """Performs one singular action, `None` for no valid action."""

        # 1. Try to Fire first (Aggressive Heuristic)
        for unit_id, unit in self._gs.query(CombatUnit):
            if (
                unit.faction != self._faction
                or unit.status == CombatUnit.Status.SUPPRESSED
            ):
                continue

            # Find targets
            for target_id, target in self._gs.query(CombatUnit):
                if target.faction == self._faction:
                    continue

                # Check validation (includes LOS check)
                if not FireSystem.validate_fire_actors(self._gs, unit_id, target_id):
                    # We have a shot! Take it.
                    result = FireSystem.fire(self._gs, unit_id, target_id)
                    if not isinstance(result, InvalidAction):
                        return FireActionResult(
                            action=FireAction(unit_id, target_id),
                            result_gs=self._gs,
                            outcome=result.outcome,
                        )

        # 2. If we can't fire, move towards nearest enemy
        for unit_id, unit in self._gs.query(CombatUnit):
            if unit.faction != self._faction:
                continue

            # Find nearest enemy
            my_pos = self._gs.get_component(unit_id, Transform).position
            nearest_enemy_pos: Vec2 | None = None
            min_dist: float = float("inf")

            for target_id, target in self._gs.query(CombatUnit):
                if target.faction != self._faction:
                    target_pos = self._gs.get_component(target_id, Transform).position
                    dist = (target_pos - my_pos).length()
                    if dist < min_dist:
                        min_dist = dist
                        nearest_enemy_pos = target_pos

            # Nearest enemy found, move there
            if nearest_enemy_pos:
                # Calculate vector to enemy
                direction = (nearest_enemy_pos - my_pos).normalized()

                # Randomize distance (between 1m and 10m, or up to enemy)
                # TODO: this is very small steps. Idea: move until interrupt?
                max_step = min(10.0, min_dist - 1.0)  # Stop 1m short
                step_size = random.uniform(1.0, max(1.1, max_step))

                target_pos = my_pos + (direction * step_size)

                result = MoveSystem.move(self._gs, unit_id, target_pos)
                if not isinstance(result, InvalidAction):
                    return MoveActionResult(
                        action=MoveAction(unit_id, target_pos),
                        result_gs=self._gs,
                        reactive_fire_outcome=result.reactive_fire_outcome,
                    )

        # 3. If no moves possible (rare), skip turn logic would go here
        return None
