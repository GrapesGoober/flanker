from dataclasses import dataclass
from typing import Literal

from flanker_core.gamestate import GameState
from flanker_core.models.components import CombatUnit, Transform
from flanker_core.models.outcomes import InvalidAction
from flanker_core.systems.initiative_system import InitiativeSystem


@dataclass
class _OrientationActionResult:
    """Result of an orientation action. Contains the new facing degrees."""

    degrees: float


class OrientationSystem:
    """Static system class for handling unit orientation actions."""

    @staticmethod
    def _validate_orientation(
        gs: GameState, unit_id: int
    ) -> Literal[True] | InvalidAction:
        """Return `True` if the unit may perform an orientation action."""

        unit = gs.get_component(unit_id, CombatUnit)

        # Only ACTIVE or PINNED units can orient. SUPPRESSED units are too shaken
        # to change their facing and are treated as inactive for this action.
        if unit.status not in (
            CombatUnit.Status.ACTIVE,
            CombatUnit.Status.PINNED,
        ):
            return InvalidAction.INACTIVE_UNIT

        return True

    @staticmethod
    def orient(
        gs: GameState, unit_id: int, degrees: float
    ) -> _OrientationActionResult | InvalidAction:
        """Mutator method rotates a unit to the specified heading.

        Does **not** flip initiative; orientation is considered a "free" action
        that simply updates the transform component.  However the unit still
        requires initiative to execute and cannot be suppressed.
        """

        # validation
        if reason := OrientationSystem._validate_orientation(gs, unit_id):
            if reason is not True:
                return reason
        if not InitiativeSystem.has_initiative(gs, unit_id):
            return InvalidAction.NO_INITIATIVE

        transform = gs.get_component(unit_id, Transform)
        # normalize degrees into [0, 360)
        transform.degrees = degrees % 360
        return _OrientationActionResult(degrees=transform.degrees)
