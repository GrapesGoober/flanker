import random
from core.components import CombatUnit, FireControls, Transform
from core.gamestate import GameState
from core.faction_system import FactionSystem
from core.los_system import LosSystem


class FireSystem:
    """Static class for handling firing action of combat units."""

    @staticmethod
    def fire(
        gs: GameState,
        attacker_id: int,
        target_id: int,
        is_reactive: bool = False,
    ) -> bool:
        """
        Performs fire action from attacker unit to target unit.
        Returns `True` if success.
        """

        # Check if attacker and target are valid
        if not (attacker := gs.get_component(attacker_id, CombatUnit)):
            return False
        if attacker.status != CombatUnit.Status.ACTIVE:
            return False
        if not (target := gs.get_component(target_id, CombatUnit)):
            return False
        if not (fire_controls := gs.get_component(attacker_id, FireControls)):
            return False

        # The reactive fire only allows when NOT having initiative
        if is_reactive and FactionSystem.has_initiative(gs, attacker_id):
            return False
        if not is_reactive and not FactionSystem.has_initiative(gs, attacker_id):
            return False

        # Check that the target faction is not the same as attacker
        attacker_faction = FactionSystem.get_faction_id(gs, attacker_id)
        target_faction = FactionSystem.get_faction_id(gs, target_id)
        if attacker_faction == target_faction:
            return False

        # Check if target is in line of sight
        if not LosSystem.check(gs, attacker_id, target_id):
            return False

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
            if not is_reactive:
                FactionSystem.flip_initiative(gs)
            return False
        elif outcome <= FireControls.Outcomes.PIN:
            target.status = CombatUnit.Status.PINNED
            # Only lose the initiative for failed action, not reaction
            if not is_reactive:
                FactionSystem.flip_initiative(gs)
            # Stops the move action, hence return `True`
            return True
        elif outcome <= FireControls.Outcomes.SUPPRESS:
            target.status = CombatUnit.Status.SUPPRESSED
            if is_reactive:
                FactionSystem.flip_initiative(gs)
            return True
        elif outcome <= FireControls.Outcomes.KILL:
            gs.delete_entity(target_id)
            if is_reactive:
                FactionSystem.flip_initiative(gs)
            return True
        return False

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
