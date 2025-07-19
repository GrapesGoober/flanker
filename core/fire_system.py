from dataclasses import dataclass
import random
from core.command_system import CommandSystem
from core.components import CombatUnit, FireControls, Transform
from core.gamestate import GameState
from core.faction_system import FactionSystem
from core.los_system import LosSystem


@dataclass
class FireResult:
    is_valid: bool
    is_hit: bool = False


class FireSystem:
    """Static class for handling firing action of combat units."""

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

        # Check if attacker and target are valid
        if not (target := gs.get_component(target_id, CombatUnit)):
            raise Exception(f"Missing component {CombatUnit} for {target_id=}")
        if not (fire_controls := gs.get_component(attacker_id, FireControls)):
            raise Exception(f"Missing component {FireControls} for {attacker_id=}")
        if not (attacker := gs.get_component(attacker_id, CombatUnit)):
            raise Exception(f"Missing component {CombatUnit} for {attacker_id=}")
        if attacker.status != CombatUnit.Status.ACTIVE:
            return FireResult(is_valid=False)

        # The reactive fire only allows when NOT having initiative
        if is_reactive and FactionSystem.has_initiative(gs, attacker_id):
            return FireResult(is_valid=False)
        if not is_reactive and not FactionSystem.has_initiative(gs, attacker_id):
            return FireResult(is_valid=False)

        # Check that the target faction is not the same as attacker
        attacker_faction = FactionSystem.get_faction_id(gs, attacker_id)
        target_faction = FactionSystem.get_faction_id(gs, target_id)
        if attacker_faction == target_faction:
            return FireResult(is_valid=False)

        # Check if target is in line of sight
        if not LosSystem.check(gs, attacker_id, target_id):
            return FireResult(is_valid=False)

        # Determine fire outcome, using overriden value if found
        if fire_controls.override:
            outcome = float(fire_controls.override)
        else:
            outcome = random.random()

        # Apply outcome
        # TODO: for fire reaction, should support multiple shooter
        if outcome <= FireControls.Outcomes.MISS:
            if is_reactive:
                fire_controls.can_reactive_fire = False
            FactionSystem.set_initiative(gs, target_faction)
            return FireResult(is_valid=True, is_hit=False)
        elif outcome <= FireControls.Outcomes.PIN:
            target.status = CombatUnit.Status.PINNED
            FactionSystem.set_initiative(gs, target_faction)
            return FireResult(is_valid=True, is_hit=True)
        elif outcome <= FireControls.Outcomes.SUPPRESS:
            target.status = CombatUnit.Status.SUPPRESSED
            FactionSystem.set_initiative(gs, attacker_faction)
            return FireResult(is_valid=True, is_hit=True)
        elif outcome <= FireControls.Outcomes.KILL:
            CommandSystem.kill_unit(gs, target_id)
            FactionSystem.set_initiative(gs, attacker_faction)
            return FireResult(is_valid=True, is_hit=True)
        return FireResult(is_valid=False)

    @staticmethod
    def get_spotter(gs: GameState, unit_id: int) -> int | None:
        """Get the a valid spotter for reactive fire, including LOS check."""

        # Check interrupt valid
        if not gs.get_component(unit_id, Transform):
            return None
        if not (unit := gs.get_component(unit_id, CombatUnit)):
            return None

        for spotter_id, spotter_unit, _, fire_controls in gs.query(
            CombatUnit, Transform, FireControls
        ):

            # Check that spotter is a valid spotter for reactive fire
            if spotter_id == unit_id:
                continue
            if unit.command_id == spotter_unit.command_id:
                continue
            if fire_controls.can_reactive_fire == False:
                continue
            if not LosSystem.check(gs, spotter_id, unit_id):
                continue

            return spotter_id

        return None
