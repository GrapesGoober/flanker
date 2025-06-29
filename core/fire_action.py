from core.components import CombatUnit
from core.gamestate import GameState
from core.command import Command
from core.los_check import LosChecker


class FireAction:
    """Static class for handling firing action of combat units."""

    @staticmethod
    def fire(gs: GameState, attacker_id: int, target_id: int) -> bool:
        """Performs fire action from attacker unit to target."""

        # Check if attacker and target are valid
        if not (attacker := gs.get_component(attacker_id, CombatUnit)):
            return False
        if attacker.status != CombatUnit.Status.ACTIVE:
            return False
        if not (target := gs.get_component(target_id, CombatUnit)):
            return False
        if not Command.has_initiative(gs, attacker_id):
            return False

        # Check if target is in line of sight
        if not LosChecker.check(gs, attacker_id, target_id):
            return False

        # Suppress the target if it survives
        # Will need to improve this with more robust RNG
        target.status = CombatUnit.Status.SUPPRESSED
        return True
