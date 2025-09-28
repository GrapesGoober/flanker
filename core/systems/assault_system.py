import random
from core.action_models import AssaultAction, AssaultActionResult, MoveAction
from core.components import (
    AssaultControls,
    CombatUnit,
    Transform,
)
from core.gamestate import GameState
from core.systems.initiative_system import InitiativeSystem
from core.systems.move_system import MoveSystem
from core.systems.command_system import CommandSystem


class AssaultSystem:
    """Static system class for handling assault action of combat units."""

    @staticmethod
    def assault(gs: GameState, action: AssaultAction) -> AssaultActionResult | None:
        """Mutator method performs assault action with reactive fire."""

        attacker_unit = gs.get_component(action.attacker_id, CombatUnit)
        target_unit = gs.get_component(action.target_id, CombatUnit)
        attacker_assault = gs.get_component(action.attacker_id, AssaultControls)
        target_position = gs.get_component(action.target_id, Transform).position

        # Check assault action valid
        if attacker_unit.status != CombatUnit.Status.ACTIVE:
            return None
        if not InitiativeSystem.has_initiative(gs, action.attacker_id):
            return None
        if attacker_unit.faction == target_unit.faction:
            return None

        # Moves the unit to target position (allow reactive fire)
        result = MoveSystem.move(gs, MoveAction(action.attacker_id, target_position))
        if result == None:
            return None
        if result.reactive_fire_outcome != None:
            return AssaultActionResult(
                reactive_fire_outcome=result.reactive_fire_outcome
            )

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
            CommandSystem.kill_unit(gs, action.target_id)
            return AssaultActionResult(outcome=AssaultControls.Outcomes.SUCCESS)
        else:
            CommandSystem.kill_unit(gs, action.attacker_id)
            return AssaultActionResult(outcome=AssaultControls.Outcomes.FAIL)
