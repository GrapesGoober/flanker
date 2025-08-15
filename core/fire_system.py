from dataclasses import dataclass
import random
from core.command_system import CommandSystem
from core.components import CombatUnit, FireControls, Transform
from core.gamestate import GameState
from core.initiative_system import InitiativeSystem
from core.los_system import LosSystem


@dataclass
class FireResult:
    """Result of a fire action as valid or successfully hit."""

    is_valid: bool
    is_hit: bool = False


class FireSystem:
    """Static class for handling firing action of combat units."""

    @staticmethod
    def _validate_fire_action(
        gs: GameState,
        attacker_id: int,
        target_id: int,
        is_reactive: bool,
    ) -> bool:

        attacker_unit = gs.get_component(attacker_id, CombatUnit)
        target_unit = gs.get_component(target_id, CombatUnit)

        # Check if attacker can attack
        if attacker_unit.status not in (
            CombatUnit.Status.ACTIVE,
            CombatUnit.Status.PINNED,
        ):
            return False
        if is_reactive and InitiativeSystem.has_initiative(gs, attacker_id):
            return False  # No initiative for reactive fire
        if not is_reactive and not InitiativeSystem.has_initiative(gs, attacker_id):
            return False

        # Check that the target faction is not the same as attacker
        if attacker_unit.faction == target_unit.faction:
            return False

        # Check if target is in line of sight
        if not LosSystem.check(gs, attacker_id, target_id):
            return False

        return True

    @staticmethod
    def fire(
        gs: GameState,
        attacker_id: int,
        target_id: int,
        is_reactive: bool = False,
    ) -> FireResult:
        """
        Performs fire action from attacker unit to target unit.
        Returns `True` if success.
        """

        if not FireSystem._validate_fire_action(
            gs, attacker_id, target_id, is_reactive
        ):
            return FireResult(is_valid=False)

        target_unit = gs.get_component(target_id, CombatUnit)
        attacker_unit = gs.get_component(attacker_id, CombatUnit)
        fire_controls = gs.get_component(attacker_id, FireControls)

        # Determine fire outcome, using overriden value if found
        if fire_controls.override:
            outcome = float(fire_controls.override)
        else:
            outcome = random.uniform(0, 1)

        # Apply outcome
        # TODO: for fire reaction, should support multiple shooter
        if outcome <= FireControls.Outcomes.MISS:
            if is_reactive:
                fire_controls.can_reactive_fire = False
            InitiativeSystem.set_initiative(gs, target_unit.faction)
            return FireResult(is_valid=True, is_hit=False)
        elif outcome <= FireControls.Outcomes.PIN:
            if target_unit.status != CombatUnit.Status.SUPPRESSED:
                target_unit.status = CombatUnit.Status.PINNED
            InitiativeSystem.set_initiative(gs, target_unit.faction)
            return FireResult(is_valid=True, is_hit=True)
        elif outcome <= FireControls.Outcomes.SUPPRESS:
            target_unit.status = CombatUnit.Status.SUPPRESSED
            InitiativeSystem.set_initiative(gs, attacker_unit.faction)
            return FireResult(is_valid=True, is_hit=True)
        elif outcome <= FireControls.Outcomes.KILL:
            CommandSystem.kill_unit(gs, target_id)
            InitiativeSystem.set_initiative(gs, attacker_unit.faction)
            return FireResult(is_valid=True, is_hit=True)
        return FireResult(is_valid=False)

    @staticmethod
    def get_spotter(gs: GameState, unit_id: int) -> int | None:
        """Get the a valid spotter for reactive fire, including LOS check."""

        unit = gs.get_component(unit_id, CombatUnit)
        for spotter_id, spotter_unit, _, fire_controls in gs.query(
            CombatUnit, Transform, FireControls
        ):

            # Check that spotter is a valid spotter for reactive fire
            if spotter_id == unit_id:
                continue
            if unit.faction == spotter_unit.faction:
                continue
            if fire_controls.can_reactive_fire == False:
                continue
            if not LosSystem.check(gs, spotter_id, unit_id):
                continue

            return spotter_id

        return None
