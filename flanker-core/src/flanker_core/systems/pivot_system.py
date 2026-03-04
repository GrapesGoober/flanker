from dataclasses import dataclass
from typing import Literal

from flanker_core.gamestate import GameState
from flanker_core.models.components import CombatUnit, Transform
from flanker_core.models.outcomes import InvalidAction
from flanker_core.systems.initiative_system import InitiativeSystem


@dataclass
class _PivotActionResult:
    """Result of a pivot action. Contains the new facing degrees."""

    degrees: float


class PivotSystem:
    """Static system class for handling unit pivot actions."""

    @staticmethod
    def _validate_pivot(
        gs: GameState, unit_id: int
    ) -> Literal[True] | InvalidAction:
        """Return `True` if the unit may perform a pivot action."""

        unit = gs.get_component(unit_id, CombatUnit)

        # Only ACTIVE or PINNED units can pivot. SUPPRESSED units are too shaken
        # to change their facing and are treated as inactive for this action.
        if unit.status not in (
            CombatUnit.Status.ACTIVE,
            CombatUnit.Status.PINNED,
        ):
            return InvalidAction.INACTIVE_UNIT

        return True

    @staticmethod
    def pivot(
        gs: GameState, unit_id: int, degrees: float
    ) -> _PivotActionResult | InvalidAction:
        """Mutator method rotates a unit to the specified heading.

        Does **not** flip initiative; pivoting is considered a "free" action
        that simply updates the transform component.  However the unit still
        requires initiative to execute and cannot be suppressed.
        """

        # validation
        if reason := PivotSystem._validate_pivot(gs, unit_id):
            if reason is not True:
                return reason
        if not InitiativeSystem.has_initiative(gs, unit_id):
            return InvalidAction.NO_INITIATIVE

        # perform reactive fire check at current position (identical to move
        # but with zero travel vector)
        from flanker_core.systems.move_system import MoveSystem
        from flanker_core.systems.fire_system import FireSystem
        from flanker_core.models.components import FireControls
        from flanker_core.models.outcomes import FireOutcomes
        from flanker_core.systems.command_system import CommandSystem

        unit = gs.get_component(unit_id, CombatUnit)
        transform = gs.get_component(unit_id, Transform)

        interrupt_candidates = MoveSystem._get_interrupt_candidates(
            gs, unit_id, transform.position
        )

        # loop through interrupt candidates exactly as move does
        for interrupt_pos, spotter_id in interrupt_candidates:
            outcome = FireSystem.get_fire_outcome(gs, spotter_id)
            match outcome:
                case FireOutcomes.MISS:
                    fire_controls = gs.get_component(spotter_id, FireControls)
                    fire_controls.can_reactive_fire = False
                    continue
                case FireOutcomes.PIN:
                    unit.status = CombatUnit.Status.PINNED
                case FireOutcomes.SUPPRESS:
                    unit.status = CombatUnit.Status.SUPPRESSED
                case FireOutcomes.KILL:
                    CommandSystem.kill_unit(gs, unit_id)
            # reactive fire interrupt stops further processing
            return _PivotActionResult(degrees=transform.degrees)

        # apply pivot now that reactive fire (if any) has been resolved
        transform.degrees = degrees % 360
        return _PivotActionResult(degrees=transform.degrees)
