import random
from core.action_models import (
    AssaultOutcomes,
    FireOutcomes,
    InvalidActionTypes,
)
from core.components import (
    AssaultControls,
    CombatUnit,
    Transform,
)
from core.gamestate import GameState
from core.systems.initiative_system import InitiativeSystem
from core.systems.move_system import MoveSystem
from core.systems.command_system import CommandSystem
from dataclasses import dataclass

_ASSAULT_SUCCESS_PROBABILITIES = {
    CombatUnit.Status.ACTIVE: 0.5,
    CombatUnit.Status.PINNED: 0.7,
    CombatUnit.Status.SUPPRESSED: 0.95,
}


@dataclass
class _AssaultActionResult:
    """Result of an assault action as assault outcome, and any reactive fire."""

    outcome: AssaultOutcomes | None = None
    reactive_fire_outcome: FireOutcomes | None = None


class AssaultSystem:
    """Static system class for handling assault action of combat units."""

    @staticmethod
    def assault(
        gs: GameState, attacker_id: int, target_id: int
    ) -> _AssaultActionResult | InvalidActionTypes:
        """Mutator method performs assault action with reactive fire."""

        attacker_unit = gs.get_component(attacker_id, CombatUnit)
        target_unit = gs.get_component(target_id, CombatUnit)
        attacker_assault = gs.get_component(attacker_id, AssaultControls)
        target_position = gs.get_component(target_id, Transform).position

        # Check assault action valid
        if attacker_unit.status != CombatUnit.Status.ACTIVE:
            return InvalidActionTypes.NO_INITIATIVE
        if not InitiativeSystem.has_initiative(gs, attacker_id):
            return InvalidActionTypes.NO_INITIATIVE
        if attacker_unit.faction == target_unit.faction:
            return InvalidActionTypes.BAD_ENTITY

        # Moves the unit to target position (allow reactive fire)
        result = MoveSystem.move(gs, attacker_id, target_position)
        if isinstance(result, InvalidActionTypes):
            return result
        if result.reactive_fire_outcome != None:
            return _AssaultActionResult(
                reactive_fire_outcome=result.reactive_fire_outcome
            )

        # Once at location, do dice roll; only one can survive
        match attacker_assault.override:
            case None:
                attacker_roll = random.uniform(0, 1)
            # Allow for override to bypass RNG by fixing roll beyond threshold
            case AssaultOutcomes.FAIL:
                attacker_roll = 1
            case AssaultOutcomes.SUCCESS:
                attacker_roll = 0

        threshold = _ASSAULT_SUCCESS_PROBABILITIES[target_unit.status]

        if attacker_roll <= threshold:
            CommandSystem.kill_unit(gs, target_id)
            return _AssaultActionResult(outcome=AssaultOutcomes.SUCCESS)
        else:
            CommandSystem.kill_unit(gs, attacker_id)
            return _AssaultActionResult(outcome=AssaultOutcomes.FAIL)
