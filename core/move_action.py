from core.components import CombatUnit, TerrainFeature, MoveControls
from core.gamestate import GameState
from core.intersects import Intersects
from core.los_check import LosChecker
from core.vec2 import Vec2


class MoveAction:
    """Static class for handling movement action of combat units."""

    @staticmethod
    def move(gs: GameState, unit_id: int, to: Vec2) -> None:
        """Actively moves a unit to a positon. Susceptible to reactive fire."""

        # Check move action is valid
        if not (unit := gs.get_component(unit_id, CombatUnit)):
            return
        if unit.status != CombatUnit.Status.ACTIVE:
            return
        if not (_ := gs.get_component(unit_id, MoveControls)):
            return

        for intersect in Intersects.get(gs, unit.position, to):
            if not (intersect.feature.flag & TerrainFeature.Flag.WALKABLE):
                return

        # For each subdivision step of move line, check LoS
        STEP_SIZE = 0.1
        length = (to - unit.position).length()
        direction = (to - unit.position).normalized()
        for i in range(0, int(length / STEP_SIZE) + 1):
            step = min(STEP_SIZE, length - i * STEP_SIZE)
            unit.position += direction * step
            is_spotted = LosChecker.check_any(gs, unit_id)
            if is_spotted:  # Spotted, stop right there
                unit.status = CombatUnit.status.SUPPRESSED
                return
