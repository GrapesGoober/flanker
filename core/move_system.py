from dataclasses import dataclass
from core.components import (
    CombatUnit,
    TerrainFeature,
    MoveControls,
    Transform,
)
from core.fire_system import FireSystem
from core.gamestate import GameState
from core.initiative_system import InitiativeSystem
from core.intersect_system import IntersectSystem
from core.utils.vec2 import Vec2


@dataclass
class MoveActionResult:
    """Result of a move action whether is valid or interrupted."""

    is_valid: bool
    is_interrupted: bool = False


class MoveSystem:
    """Static system class for handling movement action of combat units."""

    @staticmethod
    def move(gs: GameState, unit_id: int, to: Vec2) -> MoveActionResult:
        """Performs move action to position; may trigger reactive fire."""

        # Check move action is valid
        transform = gs.get_component(unit_id, Transform)
        unit = gs.get_component(unit_id, CombatUnit)
        move_controls = gs.get_component(unit_id, MoveControls)

        if unit.status != CombatUnit.Status.ACTIVE:
            return MoveActionResult(is_valid=False)
        if not InitiativeSystem.has_initiative(gs, unit_id):
            return MoveActionResult(is_valid=False)

        # Check move action though correct terrain type
        terrain_type = 0
        match move_controls.move_type:
            case MoveControls.MoveType.FOOT:
                terrain_type = TerrainFeature.Flag.WALKABLE

        for intersect in IntersectSystem.get(gs, transform.position, to):
            if not (intersect.terrain.flag & terrain_type):
                return MoveActionResult(is_valid=False)

        # For each subdivision step of move line, check interrupt
        STEP_SIZE = 1
        length = (to - transform.position).length()
        direction = (to - transform.position).normalized()
        for i in range(0, int(length / STEP_SIZE) + 1):
            # Use min(); last move step will be smaller than step size
            step = min(STEP_SIZE, length - i * STEP_SIZE)
            transform.position += direction * step

            # Check for interrupt
            # TODO: for fire reaction, should support multiple shooter
            if (spotter_id := FireSystem.get_spotter(gs, unit_id)) != None:
                # Interrupt valid, perform the fire action
                fire_result = FireSystem.fire(
                    gs=gs,
                    attacker_id=spotter_id,
                    target_id=unit_id,
                    is_reactive=True,
                )
                if fire_result.is_hit:
                    return MoveActionResult(
                        is_valid=True,
                        is_interrupted=True,
                    )
        return MoveActionResult(
            is_valid=True,
            is_interrupted=False,
        )

    @staticmethod
    def batch_interrupt_check(gs: GameState):
        # STEP 1
        # Generate arrays of source and target points, [a] and [b]
        #   - Ideally the source (spotter) can be kept since it doesnt change much
        # STEP 2
        # gs.query all terrain data, prepare terrain arrays
        #   - excluding and including as masks and source terrain
        #   - might prefer a call-level cache, say, context object
        # STEP 3
        # pass this to separate njit func to process all arrays
        #   - python loops are possible, since njit can compile that
        #   - doesn't need all operations done in numpy's loop
        #   - return the index (either as np mask or py loop)
        #   - this index can be used to infer the interrupted position
        #
        # Might wanna try using cuda too once batch processing is done

        ...
