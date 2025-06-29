from core.components import (
    CombatUnit,
    TerrainFeature,
    MoveControls,
    Transform,
)
from core.fire_action import FireAction
from core.gamestate import GameState
from core.command import Command
from core.intersects import Intersects
from core.los_check import LosChecker
from core.vec2 import Vec2


class MoveAction:
    """Static class for handling movement action of combat units."""

    @staticmethod
    def move(gs: GameState, unit_id: int, to: Vec2) -> None:
        """Actively moves a unit to a positon. Susceptible to reactive fire."""

        # Check move action is valid
        if not (transform := gs.get_component(unit_id, Transform)):
            return
        if not (unit := gs.get_component(unit_id, CombatUnit)):
            return
        if unit.status != CombatUnit.Status.ACTIVE:
            return
        if not (_ := gs.get_component(unit_id, MoveControls)):
            return
        if not Command.has_initiative(gs, unit_id):
            return

        for intersect in Intersects.get(gs, transform.position, to):
            if not (intersect.feature.flag & TerrainFeature.Flag.WALKABLE):
                return

        # For each subdivision step of move line, check LoS
        STEP_SIZE = 0.1
        length = (to - transform.position).length()
        direction = (to - transform.position).normalized()
        for i in range(0, int(length / STEP_SIZE) + 1):
            step = min(STEP_SIZE, length - i * STEP_SIZE)
            transform.position += direction * step
            if MoveAction._interrupt_if_valid(gs, unit_id):
                # Move interrupted, stop move action here
                break

    @staticmethod
    def _interrupt_if_valid(gs: GameState, unit_id: int) -> bool:
        """Interrupts a move action depending on the game state."""
        if los_ctx := LosChecker.check_any(gs, unit_id):
            fire_ctx = FireAction.fire(
                gs, attacker_id=los_ctx.spotter_id, target_id=unit_id
            )
            if fire_ctx:
                Command.flip_initiative(gs)
            return True
        return False
