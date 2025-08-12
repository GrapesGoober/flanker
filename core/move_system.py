from core.components import (
    CombatUnit,
    TerrainFeature,
    MoveControls,
    Transform,
)
from core.events import MoveActionInput, MoveStepEvent
from core.gamestate import GameState
from core.faction_system import InitiativeSystem
from core.intersect_system import IntersectSystem
from test_event import EventRegistry


class MoveSystem:
    """Static system class for handling movement action of combat units."""

    @EventRegistry.on(MoveActionInput)
    @staticmethod
    def move(gs: GameState, input: MoveActionInput) -> None:
        """Actively moves a unit to a positon. Susceptible to reactive fire."""

        # Check move action is valid
        transform = gs.get_component(input.unit_id, Transform)
        unit = gs.get_component(input.unit_id, CombatUnit)
        move_controls = gs.get_component(input.unit_id, MoveControls)

        if unit.status != CombatUnit.Status.ACTIVE:
            return
        if not InitiativeSystem.has_initiative(gs, input.unit_id):
            return

        # Check move action though correct terrain type
        terrain_type = 0
        match move_controls.move_type:
            case MoveControls.MoveType.FOOT:
                terrain_type = TerrainFeature.Flag.WALKABLE

        for intersect in IntersectSystem.get(gs, transform.position, input.to):
            if not (intersect.terrain.flag & terrain_type):
                return

        # For each subdivision step of move line, check interrupt
        STEP_SIZE = 1
        length = (input.to - transform.position).length()
        direction = (input.to - transform.position).normalized()
        for i in range(0, int(length / STEP_SIZE) + 1):
            # Use min(); last move step will be smaller than step size
            step = min(STEP_SIZE, length - i * STEP_SIZE)
            transform.position += direction * step

            step_event = MoveStepEvent(input.unit_id)
            gs.events.emit(step_event)
            if step_event.is_interrupted:
                return
