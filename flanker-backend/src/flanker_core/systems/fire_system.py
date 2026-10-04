import random
from typing import Iterable
from uuid import UUID

from flanker_core.gamestate import GameState
from flanker_core.models.actions import FireActionResult
from flanker_core.models.components import CombatUnit, FireControls, Transform
from flanker_core.models.outcomes import FireEffect, FireOutcomes, InvalidAction
from flanker_core.systems.command_system import CommandSystem
from flanker_core.systems.los_system import LosSystem
from flanker_core.systems.objective_system import ObjectiveSystem

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
        attacker_id: UUID,
        target_id: UUID,
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

        # Check if attacker has LOS to target
        if not LosSystem.has_los(
            gs,
            attacker_transform.position,
            target_transform.position,
        ):
            return InvalidAction.BAD_COORDS

        # Check FOV if the attacker has FOV firing limit
        if not LosSystem.in_fov(gs, attacker_id, target_transform.position):
            return InvalidAction.BAD_COORDS

    @staticmethod
    def get_fire_outcome(
        gs: GameState,
        attacker_id: UUID,
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
    def apply_fire_outcome(
        gs: GameState,
        attacker_id: UUID,
        target_id: UUID,
        fire_outcome: FireOutcomes,
    ) -> None:
        """Applies the fire outcome to the target combat unit."""
        fire_controls = gs.get_component(attacker_id, FireControls)
        target_unit = gs.get_component(target_id, CombatUnit)

        match fire_outcome:
            case FireOutcomes.MISS:
                pass
            case FireOutcomes.PIN:
                fire_effect = FireEffect.PINNING
                fire_controls.firing_at = (target_id, fire_effect)
                FireSystem.apply_fire_effect(gs, target_id, fire_effect)
            case FireOutcomes.SUPPRESS:
                if target_unit.status != CombatUnit.Status.SUPPRESSED:
                    fire_effect = FireEffect.SUPPRESSING
                    fire_controls.firing_at = (target_id, fire_effect)
                    FireSystem.apply_fire_effect(gs, target_id, fire_effect)
                else:  # Kills the unit if it is already suppressed
                    CommandSystem.kill_unit(gs, target_id)
            case FireOutcomes.KILL:
                CommandSystem.kill_unit(gs, target_id)

    @staticmethod
    def apply_fire_effect(
        gs: GameState,
        target_id: UUID,
        fire_effect: FireEffect,
    ) -> None:
        target_unit = gs.get_component(target_id, CombatUnit)
        target_fire_controls = gs.try_component(target_id, FireControls)

        match fire_effect:
            case FireEffect.PINNING:
                if target_unit.status == CombatUnit.Status.ACTIVE:
                    target_unit.status = CombatUnit.Status.PINNED
            case FireEffect.SUPPRESSING:
                if target_unit.status in [
                    CombatUnit.Status.ACTIVE,
                    CombatUnit.Status.PINNED,
                ]:
                    target_unit.status = CombatUnit.Status.SUPPRESSED
                    if target_fire_controls != None:
                        # Reset the target's fire effect because
                        # SUPPRESSED units can't fire.
                        target_fire_controls.firing_at = None

    @staticmethod
    def fire(
        gs: GameState,
        attacker_id: UUID,
        target_id: UUID,
    ) -> FireActionResult | InvalidAction:
        """Performs a complete fire action from attacker to target unit."""

        # Validate fire actors
        if reason := FireSystem.validate_fire_actors(gs, attacker_id, target_id):
            return reason

        # Reset stall count after validity checks
        attacker_unit = gs.get_component(attacker_id, CombatUnit)
        ObjectiveSystem.reset_stall(gs, attacker_unit.faction)

        # Apply outcome
        fire_outcome = FireSystem.get_fire_outcome(gs, attacker_id)
        FireSystem.apply_fire_outcome(
            gs,
            attacker_id=attacker_id,
            target_id=target_id,
            fire_outcome=fire_outcome,
        )
        return FireActionResult(outcome=fire_outcome)

    @staticmethod
    def get_reactive_fire_candidates(gs: GameState, target_id: UUID) -> Iterable[UUID]:
        """Returns a list of valid reactive fire candidates. Doesn't check LOS."""
        unit = gs.get_component(target_id, CombatUnit)
        for spotter_id, spotter_unit, _, _ in gs.query(
            CombatUnit, Transform, FireControls
        ):
            # Check that spotter is a valid spotter for reactive fire
            if spotter_unit.status == CombatUnit.Status.SUPPRESSED:
                continue
            if spotter_id == target_id:
                continue
            if unit.faction == spotter_unit.faction:
                continue

            yield spotter_id
