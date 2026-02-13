import random

from flanker_ai.unabstracted.models import (
    ActionResult,
    FireAction,
    FireActionResult,
    MoveAction,
    MoveActionResult,
)
from flanker_core.gamestate import GameState
from flanker_core.models.components import CombatUnit, Transform
from flanker_core.models.outcomes import InvalidAction
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.fire_system import FireSystem
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.move_system import MoveSystem


class RandomHeuristicPlayer:
    """
    Random Heuristic (Baseline).
    Logic:
    1. If an enemy is in LOF, Fire.
    2. Else, move a random distance along a vector towards the nearest enemy.
    """

    # TODO: this should be implemented for full play (wait for merge?)
    @staticmethod
    def play(gs: GameState) -> ActionResult | None:
        # Get active faction
        current_faction = InitiativeSystem.get_initiative(gs)

        # 1. Try to Fire first (Aggressive Heuristic)
        for unit_id, unit in gs.query(CombatUnit):
            if (
                unit.faction != current_faction
                or unit.status == CombatUnit.Status.SUPPRESSED
            ):
                continue

            # Find targets
            for target_id, target in gs.query(CombatUnit):
                if target.faction == current_faction:
                    continue

                # Check validation (includes LOS check)
                if not FireSystem.validate_fire_actors(gs, unit_id, target_id):
                    # We have a shot! Take it.
                    result = FireSystem.fire(gs, unit_id, target_id)
                    if not isinstance(result, InvalidAction):
                        return FireActionResult(
                            action=FireAction(unit_id, target_id),
                            result_gs=gs,
                            outcome=result.outcome,
                        )

        # 2. If we can't fire, Move towards enemy
        for unit_id, unit in gs.query(CombatUnit):
            if unit.faction != current_faction:
                continue

            # Find nearest enemy
            my_pos = gs.get_component(unit_id, Transform).position
            nearest_enemy_pos: Vec2 | None = None
            min_dist: float = float("inf")

            for target_id, target in gs.query(CombatUnit):
                if target.faction != current_faction:
                    target_pos = gs.get_component(target_id, Transform).position
                    dist = (target_pos - my_pos).length()
                    if dist < min_dist:
                        min_dist = dist
                        nearest_enemy_pos = target_pos

            if nearest_enemy_pos:
                # Calculate vector to enemy
                direction = (nearest_enemy_pos - my_pos).normalized()

                # Randomize distance (between 1m and 10m, or up to enemy)
                # TODO: this is very small steps. Idea: move until interrupt?
                max_step = min(10.0, min_dist - 1.0)  # Stop 1m short
                step_size = random.uniform(1.0, max(1.1, max_step))

                target_pos = my_pos + (direction * step_size)

                result = MoveSystem.move(gs, unit_id, target_pos)
                if not isinstance(result, InvalidAction):
                    return MoveActionResult(
                        action=MoveAction(unit_id, target_pos),
                        result_gs=gs,
                        reactive_fire_outcome=result.reactive_fire_outcome,
                    )

        # 3. If no moves possible (rare), skip turn logic would go here
        return None
