from core.components import CombatUnit
from core.gamestate import GameState
from core.los_check import LosChecker


class FireAction:
    """Static class for handling firing action of combat units."""

    @staticmethod
    def fire(gs: GameState, attacker_id: int, target_id: int) -> None:
        """Handles firing action from one unit to another."""

        # Check if attacker and target are valid
        if not (attacker := gs.get_component(attacker_id, CombatUnit)):
            return
        if attacker.status != CombatUnit.Status.ACTIVE:
            return
        if not (target := gs.get_component(target_id, CombatUnit)):
            return

        # Check if target is in line of sight
        if not LosChecker.can_see(gs, attacker_id, target_id):
            return

        # Suppress the target if it survives
        target.status = CombatUnit.Status.SUPPRESSED
