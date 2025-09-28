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


class FireSystem:
    """Static class for handling firing action of combat units."""

    @staticmethod
    def validate_fire_actors(
        gs: GameState,
        attacker_id: int,
        target_id: int,
    ) -> bool:
        """Validates that attacker can fire at target. Doesn't Check initiative."""

        attacker_unit = gs.get_component(attacker_id, CombatUnit)
        target_unit = gs.get_component(target_id, CombatUnit)
        target_transform = gs.get_component(target_id, Transform)

        # Check if attacker can attack
        if attacker_unit.status not in (
            CombatUnit.Status.ACTIVE,
            CombatUnit.Status.PINNED,
        ):
            return False

        # Check that the target faction is not the same as attacker
        if attacker_unit.faction == target_unit.faction:
            return False

        # Check if target is in line of sight
        if not LosSystem.check(gs, attacker_id, target_transform.position):
            return False

        return True

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
        else:
            outcome = random.uniform(0, 1)

        # Apply outcome
        if outcome <= FireControls.OutcomesProbabilityRanges.MISS:
            return FireOutcomes.MISS
        elif outcome <= FireControls.OutcomesProbabilityRanges.PIN:
            return FireOutcomes.PIN
        elif outcome <= FireControls.OutcomesProbabilityRanges.SUPPRESS:
            return FireOutcomes.SUPPRESS
        elif outcome <= FireControls.OutcomesProbabilityRanges.KILL:
            return FireOutcomes.KILL

        raise Exception(f"Invalid value {outcome=}")

    @staticmethod
    def fire(
        gs: GameState, action: FireAction
    ) -> FireActionResult | InvalidActionTypes:
        """Mutator method performs fire action from attacker unit to target unit."""

        # Validate fire actors
        if not FireSystem.validate_fire_actors(
            gs, action.attacker_id, action.target_id
        ):
            return InvalidActionTypes.BAD_ENTITY
        if not InitiativeSystem.has_initiative(gs, action.attacker_id):
            return InvalidActionTypes.BAD_INITIATIVE

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
