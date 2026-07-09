from typing import overload

from flanker_core.gamestate import GameState
from flanker_core.models.actions import (
    Action,
    ActionResult,
    AssaultAction,
    AssaultActionResult,
    FireAction,
    FireActionResult,
    MoveAction,
    MoveActionResult,
    PivotAction,
    PivotActionResult,
)
from flanker_core.models.outcomes import InvalidAction
from flanker_core.systems.assault_system import AssaultSystem
from flanker_core.systems.fire_system import FireSystem
from flanker_core.systems.move_system import MoveSystem


class ActionSystem:
    """
    Static system class to perform all in-game actions.
    This acts as an entry point to dispatch to each system calls.
    """

    @overload
    @staticmethod
    def perform(
        gs: GameState, action: MoveAction
    ) -> MoveActionResult | InvalidAction: ...

    @overload
    @staticmethod
    def perform(
        gs: GameState, action: PivotAction
    ) -> PivotActionResult | InvalidAction: ...

    @overload
    @staticmethod
    def perform(
        gs: GameState, action: FireAction
    ) -> FireActionResult | InvalidAction: ...

    @overload
    @staticmethod
    def perform(
        gs: GameState, action: AssaultAction
    ) -> AssaultActionResult | InvalidAction: ...

    @staticmethod
    def perform(
        gs: GameState,
        action: Action,
    ) -> ActionResult | InvalidAction:
        """Performs an action."""

        match action:
            case MoveAction():
                return MoveSystem.move(gs, action.unit_id, action.to)
            case PivotAction():
                return MoveSystem.pivot(gs, action.unit_id, action.to)
            case FireAction():
                return FireSystem.fire(gs, action.unit_id, action.target_id)
            case AssaultAction():
                return AssaultSystem.assault(gs, action.unit_id, action.target_id)
