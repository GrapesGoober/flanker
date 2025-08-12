from core.components import (
    CombatUnit,
    TerrainFeature,
    MoveControls,
    Transform,
)
from core.events import MoveActionInput
from core.fire_system import FireSystem
from core.gamestate import GameState
from core.faction_system import InitiativeSystem
from core.intersect_system import IntersectSystem
from test_event import EventRegistry


class MoveSystem:
    """Static system class for handling movement action of combat units."""

    @staticmethod
    @EventRegistry.on(MoveActionInput)
    def move(gs: GameState, event: MoveActionInput) -> None:
        """Actively moves a unit to a positon. Susceptible to reactive fire."""

        # Check move action is valid
        transform = gs.get_component(event.unit_id, Transform)
        unit = gs.get_component(event.unit_id, CombatUnit)
        move_controls = gs.get_component(event.unit_id, MoveControls)

        if unit.status != CombatUnit.Status.ACTIVE:
            return
        if not InitiativeSystem.has_initiative(gs, event.unit_id):
            return

        # Check move action though correct terrain type
        terrain_type = 0
        match move_controls.move_type:
            case MoveControls.MoveType.FOOT:
                terrain_type = TerrainFeature.Flag.WALKABLE

        for intersect in IntersectSystem.get(gs, transform.position, event.to):
            if not (intersect.terrain.flag & terrain_type):
                return

        # For each subdivision step of move line, check interrupt
        STEP_SIZE = 1
        length = (event.to - transform.position).length()
        direction = (event.to - transform.position).normalized()
        for i in range(0, int(length / STEP_SIZE) + 1):
            # Use min(); last move step will be smaller than step size
            step = min(STEP_SIZE, length - i * STEP_SIZE)
            transform.position += direction * step

            # Check for interrupt
            # TODO: for fire reaction, should support multiple shooter
            if (spotter_id := FireSystem.get_spotter(gs, event.unit_id)) != None:
                # Interrupt valid, perform the fire action
                fire_result = FireSystem.fire(
                    gs=gs,
                    attacker_id=spotter_id,
                    target_id=event.unit_id,
                    is_reactive=True,
                )
                if fire_result.is_hit:
                    return
