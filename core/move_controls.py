import esper
from components import MovementControls, Transform, UnitCondition
from intersects import Intersects
from los_check import LosChecker
from terrain_types import TerrainFlag
from vec2 import Vec2

_MOVE_COMPONENTS = Transform, MovementControls, UnitCondition
_MOVE_COMPONENTS_T = tuple[Transform, MovementControls, UnitCondition]


def get_components(unit_id: int) -> _MOVE_COMPONENTS_T | None:
    return esper.try_components(unit_id, *_MOVE_COMPONENTS)


class MoveControls:
    @staticmethod
    def move(unit_id: int, to: Vec2) -> None:

        # Check component dependency
        if not (comps := get_components(unit_id)):
            return
        transform, _, cond = comps

        # Check move action is valid
        if cond.status != UnitCondition.Status.ACTIVE:
            return
        for intersect in Intersects.get(transform.position, to):
            if not (intersect.feature.flag & TerrainFlag.WALKABLE):
                return

        # For each subdivision step of move line, check LoS
        STEP_SIZE = 0.1
        length = (to - transform.position).length()
        direction = (to - transform.position).normalized()
        for i in range(0, int(length / STEP_SIZE) + 1):
            step = min(STEP_SIZE, length - i * STEP_SIZE)
            transform.position += direction * step
            is_spotted = LosChecker.is_spotted(unit_id)
            if is_spotted:  # Spotted, stop right there
                cond.status = UnitCondition.status.SUPPRESSED
                return
