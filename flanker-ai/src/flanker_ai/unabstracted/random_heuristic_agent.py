import random
import math
from copy import deepcopy

from flanker_ai.unabstracted.models import (
    ActionResult,
    FireAction,
    FireActionResult,
    MoveAction,
    MoveActionResult,
    OrientationAction,
    OrientationActionResult,
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

            # before firing, make sure we're facing the enemy; orient if needed
            # find nearest enemy for this unit
            my_pos = self._gs.get_component(unit_id, Transform).position
            best_target: int | None = None
            best_dist = float("inf")
            for target_id, target in self._gs.query(CombatUnit):
                if target.faction == self._faction:
                    continue
                target_pos = self._gs.get_component(target_id, Transform).position
                dist = (target_pos - my_pos).length()
                if dist < best_dist:
                    best_dist = dist
                    best_target = target_id
            if best_target is not None:
                # compute desired heading
                target_pos = self._gs.get_component(best_target, Transform).position
                dx = target_pos.x - my_pos.x
                dy = target_pos.y - my_pos.y
                desired_deg = (180 / 3.141592653589793) * (  # type: ignore
                    0 if dx == 0 and dy == 0 else math.atan2(dy, dx)
                )
                # normalize
                if desired_deg < 0:
                    desired_deg += 360
                current_deg = self._gs.get_component(unit_id, Transform).degrees
                # orient if heading differs by more than 1 degree
                if abs((desired_deg - current_deg + 180) % 360 - 180) > 1.0:
                    from flanker_core.systems.orientation_system import OrientationSystem

                    result = OrientationSystem.orient(self._gs, unit_id, desired_deg)
                    if not isinstance(result, InvalidAction):
                        return OrientationActionResult(
                            action=OrientationAction(unit_id, desired_deg),
                            result_gs=self._gs,
                        )

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
            nearest_enemy_distance: float = float("inf")

            for target_id, target in self._gs.query(CombatUnit):
                if target.faction != self._faction:
                    target_pos = self._gs.get_component(target_id, Transform).position
                    dist = (target_pos - my_pos).length()
                    if dist < nearest_enemy_distance:
                        nearest_enemy_distance = dist
                        nearest_enemy_pos = target_pos

            # Nearest enemy found, move there
            if nearest_enemy_pos:
                # Calculate vector to enemy
                direction = (nearest_enemy_pos - my_pos).normalized()

                # Randomize distance (between 1m and 10m, or up to enemy)
                # TODO: this is very small steps. Idea: move until interrupt?
                max_step = min(  # Stop 1m short
                    nearest_enemy_distance / 2, nearest_enemy_distance - 1.0
                )
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
