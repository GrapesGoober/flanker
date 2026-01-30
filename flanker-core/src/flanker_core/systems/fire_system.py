import random
from dataclasses import dataclass
from typing import Iterable

from flanker_core.gamestate import GameState
from flanker_core.models.components import CombatUnit, FireControls, Transform
from flanker_core.models.outcomes import FireOutcomes, InvalidAction
from flanker_core.systems.command_system import CommandSystem
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.los_system import LosSystem


@dataclass
class _FireActionResult:
    """Result of a fire action as outcome."""

    outcome: FireOutcomes | None = None


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
    ) -> InvalidAction | None:
        """Returns a reason if invalid, `None` otherwise. Doesn't Check initiative."""

        attacker_unit = gs.get_component(attacker_id, CombatUnit)
        attacker_transform = gs.get_component(attacker_id, Transform)
        target_unit = gs.get_component(target_id, CombatUnit)
        target_transform = gs.get_component(target_id, Transform)

        # Check if attacker can attack
        if attacker_unit.status not in (
            CombatUnit.Status.ACTIVE,
            CombatUnit.Status.PINNED,
        ):
            return InvalidAction.INACTIVE_UNIT

        # Check that the target faction is not the same as attacker
        if attacker_unit.faction == target_unit.faction:
            return InvalidAction.BAD_ENTITY

        # Check if target is in line of sight
        if not LosSystem.check(
            gs, attacker_transform.position, target_transform.position
        ):
            return InvalidAction.BAD_COORDS

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
        gs: GameState,
        attacker_id: int,
        target_id: int,
    ) -> _FireActionResult | InvalidAction:
        """Mutator method performs fire action from attacker unit to target unit."""

        # Validate fire actors
        if reason := FireSystem.validate_fire_actors(gs, attacker_id, target_id):
            return reason
        if not InitiativeSystem.has_initiative(gs, attacker_id):
            return InvalidAction.NO_INITIATIVE

        # Apply outcome
        target_unit = gs.get_component(target_id, CombatUnit)
        match FireSystem.get_fire_outcome(gs, attacker_id):
            case FireOutcomes.MISS:
                InitiativeSystem.set_initiative(gs, target_unit.faction)
                return _FireActionResult(outcome=FireOutcomes.MISS)
            case FireOutcomes.PIN:
                if target_unit.status != CombatUnit.Status.SUPPRESSED:
                    target_unit.status = CombatUnit.Status.PINNED
                InitiativeSystem.set_initiative(gs, target_unit.faction)
                return _FireActionResult(outcome=FireOutcomes.PIN)
            case FireOutcomes.SUPPRESS:
                if target_unit.status != CombatUnit.Status.SUPPRESSED:
                    target_unit.status = CombatUnit.Status.SUPPRESSED
                    return _FireActionResult(outcome=FireOutcomes.SUPPRESS)
                else:  # Kills the unit if it is already suppressed
                    CommandSystem.kill_unit(gs, target_id)
                    return _FireActionResult(outcome=FireOutcomes.KILL)
            case FireOutcomes.KILL:
                CommandSystem.kill_unit(gs, target_id)
                return _FireActionResult(outcome=FireOutcomes.KILL)

    @staticmethod
    def get_spotter_candidates(gs: GameState, target_id: int) -> Iterable[int]:
        """Returns a list of valid spotters for reactive fire. Doesn't check LOS."""

        unit = gs.get_component(target_id, CombatUnit)
        for spotter_id, spotter_unit, _, fire_controls in gs.query(
            CombatUnit, Transform, FireControls
        ):
            # Check that spotter is a valid spotter for reactive fire
            if spotter_unit.status == CombatUnit.Status.SUPPRESSED:
                continue
            if spotter_id == target_id:
                continue
            if unit.faction == spotter_unit.faction:
                continue
            if fire_controls.can_reactive_fire == False:
                continue

            yield spotter_id
