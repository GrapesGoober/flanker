import random
from core.components import CombatUnit, FireControls
from core.gamestate import GameState
from core.command import Command
from core.los_check import LosChecker


class FireAction:
    """Static class for handling firing action of combat units."""

    @staticmethod
    def fire(
        gs: GameState, attacker_id: int, target_id: int, ingore_initiative: bool = False
    ) -> bool:
        """Performs fire action from attacker unit to target."""

        # Check if attacker and target are valid
        if not (attacker := gs.get_component(attacker_id, CombatUnit)):
            return False
        if attacker.status != CombatUnit.Status.ACTIVE:
            return False
        if not (target := gs.get_component(target_id, CombatUnit)):
            return False
        if not (fire_controls := gs.get_component(attacker_id, FireControls)):
            return False
        if not ingore_initiative:
            if not Command.has_initiative(gs, attacker_id):
                return False

        # Check if target is in line of sight
        if not LosChecker.check(gs, attacker_id, target_id):
            return False

        # Determine fire outcome, using overriden value if found
        if fire_controls.override:
            outcome = float(fire_controls.override)
        else:
            outcome = random.random()

        # Apply outcome
        if outcome <= FireControls.Outcomes.MISS:
            return False
        elif outcome <= FireControls.Outcomes.SUPPRESS:
            target.status = CombatUnit.Status.SUPPRESSED
            return True
        elif outcome <= FireControls.Outcomes.KILL:
            gs.delete_entity(target_id)
            return True
        return False
