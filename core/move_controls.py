import esper
from components import MovementControls, Transform, UnitCondition
from intersects import Intersects
from los_check import LosChecker
from terrain_types import TerrainFlag
from vec2 import Vec2


class MoveControls:
    @staticmethod
    def move(unit_id: int, to: Vec2) -> None:

        # Check move action is valid
        if not (
            comps := esper.try_components(
                unit_id, Transform, MovementControls, UnitCondition
            )
        ):
            return
        transform, _, cond = comps

        if cond.status != UnitCondition.Status.ACTIVE:
            return
        for intersect in Intersects.get(transform.position, to):
            if not (intersect.feature.flag & TerrainFlag.WALKABLE):
                return

        # For each subdivision step of move line, check LoS
        STEP_SIZE = 0.1
        length = (to - transform.position).length()
        direction = (to - transform.position).normalized()
        for step in range(int(length / STEP_SIZE) - 1):
            transform.position += direction * STEP_SIZE
            is_spotted = LosChecker.is_spotted(unit_id)
            if is_spotted:  # Spotted, stop right there
                cond.status = UnitCondition.status.SUPPRESSED
                return

        # Not spotted, move to destination
        transform.position = to
