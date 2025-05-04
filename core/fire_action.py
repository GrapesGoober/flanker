from core.components import UnitCondition
from core.los_check import LosChecker
import esper


class FireAction:
    """Static class for handling firing action of combat units."""

    @staticmethod
    def fire(attacker_id: int, target_id: int) -> None:
        """Handles firing action from one unit to another."""

        # Check if attacker and target are valid
        if not (attacker := esper.try_component(attacker_id, UnitCondition)):
            return
        if attacker.status != UnitCondition.Status.ACTIVE:
            return
        if not (target := esper.try_component(target_id, UnitCondition)):
            return

        # Check if target is in line of sight
        if not LosChecker.can_see(attacker_id, target_id):
            return

        # Suppress the target if it survives
        target.status = UnitCondition.Status.SUPPRESSED
