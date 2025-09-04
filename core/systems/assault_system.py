from dataclasses import dataclass
import random
from core.components import (
    AssaultControls,
    CombatUnit,
    Transform,
)
from core.gamestate import GameState
from core.systems.initiative_system import InitiativeSystem
from core.systems.move_system import MoveSystem
from core.systems.command_system import CommandSystem


@dataclass
class AssaultActionResult:
    is_valid: bool = True
    is_interrupted: bool = False
    result: AssaultControls.Outcomes | None = None


class AssaultSystem:
    """Static system class for handling movement action of combat units."""

    @staticmethod
    def assault(
        gs: GameState,
        attacker_id: int,
        target_id: int,
    ) -> AssaultActionResult:
        """Performs assault action to target; may trigger reactive fire."""
        attacker_unit = gs.get_component(attacker_id, CombatUnit)
        target_unit = gs.get_component(target_id, CombatUnit)
        attacker_assault = gs.get_component(attacker_id, AssaultControls)
        target_transform = gs.get_component(target_id, Transform)

        # Check assault action valid
        if attacker_unit.status != CombatUnit.Status.ACTIVE:
            return AssaultActionResult(is_valid=False)
        if not InitiativeSystem.has_initiative(gs, attacker_id):
            return AssaultActionResult(is_valid=False)
        if attacker_unit.faction == target_unit.faction:
            return AssaultActionResult(is_valid=False)

        # Moves the unit to target position (allow reactive fire)
        result = MoveSystem.move(gs, attacker_id, target_transform.position)
        if not result.is_valid:
            return AssaultActionResult(is_valid=False)
        if result.is_interrupted:
            return AssaultActionResult(is_interrupted=True)

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
            return AssaultActionResult(result=AssaultControls.Outcomes.SUCCESS)
        else:
            CommandSystem.kill_unit(gs, attacker_id)
            return AssaultActionResult(result=AssaultControls.Outcomes.FAIL)
