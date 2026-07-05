import random
from dataclasses import dataclass
from typing import Iterable
from uuid import UUID

from flanker_core.gamestate import GameState
from flanker_core.models.components import CombatUnit, FireControls, Transform
from flanker_core.models.outcomes import FireEffect, FireOutcomes, InvalidAction
from flanker_core.systems.command_system import CommandSystem
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.los_system import LosSystem
from flanker_core.systems.objective_system import ObjectiveSystem


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
    def get_status(
        gs: GameState,
        unit_id: UUID,
    ) -> CombatUnit.Status:
        """Gets the current unit status of a combat unit."""

        unit = gs.get_component(unit_id, CombatUnit)

        # If overriden, return the override value
        if unit.status_override != None:
            return unit.status_override

        # Record each fire effects of each firer
        fire_effects: set[FireEffect] = set()
        for _, fire_controls in gs.query(FireControls):
            if fire_controls.firing_at == None:
                continue
            fire_at_id, fire_effect = fire_controls.firing_at
            if fire_at_id != unit_id:
                continue
            fire_effects.add(fire_effect)

        # Apply each fire effect; SUPPRESSING surpass PINNING
        if FireEffect.SUPPRESSING in fire_effects:
            return CombatUnit.Status.SUPPRESSED
        elif fire_effects == {FireEffect.PINNING}:
            return CombatUnit.Status.PINNED

        # No fire effect => return active status
        return CombatUnit.Status.ACTIVE

    @staticmethod
    def validate_fire_actors(
        gs: GameState,
        attacker_id: UUID,
        target_id: UUID,
    ) -> InvalidAction | None:
        """Returns a reason if invalid, `None` otherwise. Doesn't Check initiative."""
        los_system = gs.get(LosSystem)
        attacker_unit = gs.get_component(attacker_id, CombatUnit)
        attacker_transform = gs.get_component(attacker_id, Transform)
        target_unit = gs.get_component(target_id, CombatUnit)
        target_transform = gs.get_component(target_id, Transform)

        # Check if attacker can attack
        if FireSystem.get_status(gs, attacker_id) not in (
            CombatUnit.Status.ACTIVE,
            CombatUnit.Status.PINNED,
        ):
            return InvalidAction.INACTIVE_UNIT

        # Check that the target faction is not the same as attacker
        if attacker_unit.faction == target_unit.faction:
            return InvalidAction.BAD_ENTITY

        # Check if attacker has LOS to target and within FOV
        if not los_system.has_los(
            gs,
            attacker_transform.position,
            target_transform.position,
        ):
            return InvalidAction.BAD_COORDS
        if not los_system.in_fov(
            attacker_transform,
            target_transform.position,
        ):
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
        command_system = gs.get(CommandSystem)
        fire_controls = gs.get_component(attacker_id, FireControls)
        target_fire_controls = gs.try_component(target_id, FireControls)

        match fire_outcome:
            case FireOutcomes.MISS:
                pass
            case FireOutcomes.PIN:
                # If firing at the same suppressed target, don't reset the effect
                if fire_controls.firing_at != (target_id, FireEffect.SUPPRESSING):
                    fire_controls.firing_at = (target_id, FireEffect.PINNING)
            case FireOutcomes.SUPPRESS:
                target_status = FireSystem.get_status(gs, target_id)
                if target_status != CombatUnit.Status.SUPPRESSED:
                    fire_controls.firing_at = (target_id, FireEffect.SUPPRESSING)
                    # Reset fire effect because SUPPRESSED unit can't fire.
                    if target_fire_controls != None:
                        target_fire_controls.firing_at = None
                else:  # Kills the unit if it is already suppressed
                    command_system.kill_unit(gs, target_id)
            case FireOutcomes.KILL:
                command_system.kill_unit(gs, target_id)

    @staticmethod
    def fire(
        gs: GameState,
        attacker_id: UUID,
        target_id: UUID,
    ) -> _FireActionResult | InvalidAction:
        """Mutator method performs fire action from attacker unit to target unit."""
        initiative_system = gs.get(InitiativeSystem)
        # Validate fire actors
        if reason := FireSystem.validate_fire_actors(gs, attacker_id, target_id):
            return reason
        if not initiative_system.has_initiative(gs, attacker_id):
            return InvalidAction.NO_INITIATIVE

        # Reset stall count after validity checks
        attacker_unit = gs.get_component(attacker_id, CombatUnit)
        ObjectiveSystem.reset_stall(gs, attacker_unit.faction)

        # Apply outcome
        target_unit = gs.get_component(target_id, CombatUnit)
        fire_outcome = FireSystem.get_fire_outcome(gs, attacker_id)
        FireSystem.apply_fire_outcome(
            gs,
            attacker_id=attacker_id,
            target_id=target_id,
            fire_outcome=fire_outcome,
        )
        match fire_outcome:
            case FireOutcomes.MISS | FireOutcomes.PIN:
                initiative_system.set_initiative(gs, target_unit.faction)
            case FireOutcomes.SUPPRESS | FireOutcomes.KILL:
                pass
        return _FireActionResult(outcome=fire_outcome)

    @staticmethod
    def get_spotter_candidates(gs: GameState, target_id: UUID) -> Iterable[UUID]:
        """Returns a list of valid spotters for reactive fire. Doesn't check LOS."""
        unit = gs.get_component(target_id, CombatUnit)
        for spotter_id, spotter_unit, _, _ in gs.query(
            CombatUnit, Transform, FireControls
        ):
            # Check that spotter is a valid spotter for reactive fire
            if FireSystem.get_status(gs, spotter_id) == CombatUnit.Status.SUPPRESSED:
                continue
            if spotter_id == target_id:
                continue
            if unit.faction == spotter_unit.faction:
                continue

            yield spotter_id
