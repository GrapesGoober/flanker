import random
from core.components import (
    AssaultControls,
    CombatUnit,
    Transform,
)
from core.gamestate import GameState
from core.faction_system import InitiativeSystem
from core.move_system import MoveSystem
from core.tests.test_hierarchy import CommandSystem


class AssaultSystem:
    """Static system class for handling movement action of combat units."""

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
        result = MoveSystem.move(gs, attacker_id, target_transform.position)
        if not result.is_valid:
            return
        if result.is_interrupted:
            return

        # Once at location, do dice roll; only one can survive
        match attacker_assault.override:
            case None:
                attacker_roll = random.uniform(0, 1)
            # Allow for override to bypass RNG by fixing roll beyond threshold
            case AssaultControls.Outcomes.FAIL:
                attacker_roll = 1
            case AssaultControls.Outcomes.SUCCESS:
                attacker_roll = 0

        threshold = {
            CombatUnit.Status.ACTIVE: AssaultControls.SuccessChances.ACTIVE,
            CombatUnit.Status.PINNED: AssaultControls.SuccessChances.PINNED,
            CombatUnit.Status.SUPPRESSED: AssaultControls.SuccessChances.SUPPRESSED,
        }[target_unit.status]

        if attacker_roll <= threshold:
            CommandSystem.kill_unit(gs, target_id)
        else:
            CommandSystem.kill_unit(gs, attacker_id)
