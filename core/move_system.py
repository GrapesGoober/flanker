import random
from core.command_system import CommandSystem
from core.components import (
    AssaultControls,
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

    @staticmethod
    def assault(gs: GameState, attacker_id: int, target_id: int) -> None:
        """Performs assault action to target; may trigger reactive fire."""
        attacker_unit = gs.get_component(attacker_id, CombatUnit)
        target_unit = gs.get_component(target_id, CombatUnit)
        attacker_assault = gs.get_component(attacker_id, AssaultControls)
        target_transform = gs.get_component(target_id, Transform)

        # Check assault action valid
        if attacker_unit.status != CombatUnit.Status.ACTIVE:
            return
        if not InitiativeSystem.has_initiative(gs, attacker_id):
            return
        if attacker_unit.faction == target_unit.faction:
            return

        # Moves the unit to target position (allow reactive fire)
        MoveSystem.move(gs, attacker_id, target_transform.position)

        # Once at location, do dice roll; only one can survive
        match attacker_assault.override:
            case None:
                attacker_roll = random.uniform(0, 1)
            # Allow for override to bypass RNG
            case AssaultControls.Outcomes.FAIL:
                attacker_roll = -1  # Target never rolls below 0
            case AssaultControls.Outcomes.SUCCESS:
                attacker_roll = 1  # Target never rolls above 1

        match target_unit.status:
            case CombatUnit.Status.ACTIVE:
                target_roll_multiplier = 1
            case CombatUnit.Status.PINNED:
                target_roll_multiplier = 0.3
            case CombatUnit.Status.SUPPRESSED:
                target_roll_multiplier = 0.05
        target_roll = random.uniform(0, target_roll_multiplier)

        if attacker_roll >= target_roll:
            CommandSystem.kill_unit(gs, target_id)
        else:
            CommandSystem.kill_unit(gs, attacker_id)
