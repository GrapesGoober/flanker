import random
from typing import Iterable
from core.action_models import (
    FireAction,
    FireActionResult,
    FireOutcomes,
    InvalidActionTypes,
)
from core.systems.command_system import CommandSystem
from core.components import CombatUnit, FireControls, Transform
from core.gamestate import GameState
from core.systems.initiative_system import InitiativeSystem
from core.systems.los_system import LosSystem

_FIRE_OUTCOME_PROBABILITIES = {
    FireOutcomes.MISS: 0.3,
    FireOutcomes.PIN: 0.4,
    FireOutcomes.SUPPRESS: 0.25,
    FireOutcomes.KILL: 0.05,
}


class FireSystem:
    """Static class for handling firing action of combat units."""

    @staticmethod
    def validate_fire_actors(
        gs: GameState,
        attacker_id: int,
        target_id: int,
    ) -> InvalidActionTypes | None:
        """Returns a reason if invalid, `None` otherwise. Doesn't Check initiative."""

        attacker_unit = gs.get_component(attacker_id, CombatUnit)
        target_unit = gs.get_component(target_id, CombatUnit)
        target_transform = gs.get_component(target_id, Transform)

        # Check if attacker can attack
        if attacker_unit.status not in (
            CombatUnit.Status.ACTIVE,
            CombatUnit.Status.PINNED,
        ):
            return InvalidActionTypes.INACTIVE_UNIT

        # Check that the target faction is not the same as attacker
        if attacker_unit.faction == target_unit.faction:
            return InvalidActionTypes.BAD_ENTITY

        # Check if target is in line of sight
        if not LosSystem.check(gs, attacker_id, target_transform.position):
            return InvalidActionTypes.BAD_COORDS

    @staticmethod
    def get_fire_outcome(
        gs: GameState,
        attacker_id: int,
    ) -> FireOutcomes:
        """Returns a new randomized fire outcome, or a fixed outcome if overridden."""

        fire_controls = gs.get_component(attacker_id, FireControls)

        # Determine fire outcome, using overriden value if found
        if fire_controls.override:
            return fire_controls.override

        # Roll outcome
        outcomes = list(_FIRE_OUTCOME_PROBABILITIES.keys())
        weights = list(_FIRE_OUTCOME_PROBABILITIES.values())
        return random.choices(outcomes, weights=weights, k=1)[0]

    @staticmethod
    def fire(
        gs: GameState, action: FireAction
    ) -> FireActionResult | InvalidActionTypes:
        """Mutator method performs fire action from attacker unit to target unit."""

        # Validate fire actors
        if reason := FireSystem.validate_fire_actors(
            gs, action.attacker_id, action.target_id
        ):
            return reason
        if not InitiativeSystem.has_initiative(gs, action.attacker_id):
            return InvalidActionTypes.NO_INITIATIVE

        # Apply outcome
        target_unit = gs.get_component(action.target_id, CombatUnit)
        match FireSystem.get_fire_outcome(gs, action.attacker_id):
            case FireOutcomes.MISS:
                InitiativeSystem.set_initiative(gs, target_unit.faction)
                return FireActionResult(outcome=FireOutcomes.MISS)
            case FireOutcomes.PIN:
                if target_unit.status != CombatUnit.Status.SUPPRESSED:
                    target_unit.status = CombatUnit.Status.PINNED
                InitiativeSystem.set_initiative(gs, target_unit.faction)
                return FireActionResult(outcome=FireOutcomes.PIN)
            case FireOutcomes.SUPPRESS:
                target_unit.status = CombatUnit.Status.SUPPRESSED
                return FireActionResult(outcome=FireOutcomes.SUPPRESS)
            case FireOutcomes.KILL:
                CommandSystem.kill_unit(gs, action.target_id)
                return FireActionResult(outcome=FireOutcomes.KILL)
        return FireActionResult(is_valid=False)

    @staticmethod
    def get_spotter_candidates(gs: GameState, target_id: int) -> Iterable[int]:
        """Returns a list of valid spotters for reactive fire. Doesn't check LOS."""

        unit = gs.get_component(target_id, CombatUnit)
        for spotter_id, spotter_unit, _, fire_controls in gs.query(
            CombatUnit, Transform, FireControls
        ):

            # Check that spotter is a valid spotter for reactive fire
            if spotter_id == target_id:
                continue
            if unit.faction == spotter_unit.faction:
                continue
            if fire_controls.can_reactive_fire == False:
                continue

            yield spotter_id
