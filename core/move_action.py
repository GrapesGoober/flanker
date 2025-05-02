from core.components import MovementControls, Transform, UnitCondition, TerrainFeature
from core.world import World
from core.intersects import Intersects
from core.los_check import LosChecker
from core.vec2 import Vec2


class MoveAction:
    """Static class for handling movement action of combat units."""

    @staticmethod
    def move(world: World, unit_id: int, to: Vec2) -> None:
        """Actively moves a unit to a positon. Susceptible to reactive fire."""

        # Check move action is valid
        if not (cond := world.get_component(unit_id, UnitCondition)):
            return
        if cond.status != UnitCondition.Status.ACTIVE:
            return
        if not world.get_component(unit_id, MovementControls):
            return
        if not (transform := world.get_component(unit_id, Transform)):
            return
        for intersect in Intersects.get(world, transform.position, to):
            if not (intersect.feature.flag & TerrainFeature.Flag.WALKABLE):
                return

        # For each subdivision step of move line, check LoS
        STEP_SIZE = 0.1
        length = (to - transform.position).length()
        direction = (to - transform.position).normalized()
        for i in range(0, int(length / STEP_SIZE) + 1):
            step = min(STEP_SIZE, length - i * STEP_SIZE)
            transform.position += direction * step
            is_spotted = LosChecker.is_spotted(world, unit_id)
            if is_spotted:  # Spotted, stop right there
                cond.status = UnitCondition.status.SUPPRESSED
                return
