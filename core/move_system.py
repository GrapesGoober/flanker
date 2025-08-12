from core.components import (
    CombatUnit,
    TerrainFeature,
    MoveControls,
    Transform,
)
from core.fire_system import FireSystem
from core.gamestate import GameState
from core.faction_system import InitiativeSystem
from core.intersect_system import IntersectSystem
from core.utils.vec2 import Vec2


class MoveSystem:
    """Static system class for handling movement action of combat units."""

    @staticmethod
    def move(gs: GameState, unit_id: int, to: Vec2) -> None:
        """Performs move action to position; may trigger reactive fire."""

        # Check move action is valid
        transform = gs.get_component(unit_id, Transform)
        unit = gs.get_component(unit_id, CombatUnit)
        move_controls = gs.get_component(unit_id, MoveControls)

        if unit.status != CombatUnit.Status.ACTIVE:
            return
        if not InitiativeSystem.has_initiative(gs, unit_id):
            return

        # Check move action though correct terrain type
        terrain_type = 0
        match move_controls.move_type:
            case MoveControls.MoveType.FOOT:
                terrain_type = TerrainFeature.Flag.WALKABLE

        for intersect in IntersectSystem.get(gs, transform.position, to):
            if not (intersect.terrain.flag & terrain_type):
                return

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
                    return
