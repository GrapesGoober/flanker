from typing import overload
from uuid import UUID

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
    RallyAction,
    RallyActionResult,
)
from flanker_core.models.components import (
    CombatUnit,
    InitiativeState,
    Transform,
)
from flanker_core.models.outcomes import (
    AssaultOutcomes,
    FireOutcomes,
    InvalidAction,
)
from flanker_core.systems.assault_system import AssaultSystem
from flanker_core.systems.command_system import CommandSystem
from flanker_core.systems.fire_system import FireSystem
from flanker_core.systems.move_system import MoveSystem
from flanker_core.systems.objective_system import ObjectiveSystem


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

    @overload
    @staticmethod
    def perform(
        gs: GameState, action: RallyAction
    ) -> RallyActionResult | InvalidAction: ...

    @staticmethod
    def perform(
        gs: GameState,
        action: Action,
    ) -> ActionResult | InvalidAction:
        """Performs an action."""

        if not ActionSystem.has_initiative(gs, action.unit_id):
            return InvalidAction.NO_INITIATIVE

        match action:
            case MoveAction():
                result = MoveSystem.move(gs, action.unit_id, action.to)
                if not isinstance(result, InvalidAction):
                    if (
                        FireOutcomes.SUPPRESS in result.reactive_fire_outcomes
                        or FireOutcomes.KILL in result.reactive_fire_outcomes
                    ):
                        ObjectiveSystem.reset_rally_stall(gs)
                        ActionSystem.flip_initiative(gs)

            case PivotAction():
                result = MoveSystem.pivot(gs, action.unit_id, action.to)
                if not isinstance(result, InvalidAction):
                    if (
                        FireOutcomes.SUPPRESS in result.reactive_fire_outcomes
                        or FireOutcomes.KILL in result.reactive_fire_outcomes
                    ):
                        ObjectiveSystem.reset_rally_stall(gs)
                        ActionSystem.flip_initiative(gs)

            case FireAction():
                result = FireSystem.fire(gs, action.unit_id, action.target_id)
                if not isinstance(result, InvalidAction):
                    if result.outcome in (FireOutcomes.MISS, FireOutcomes.PIN):
                        ObjectiveSystem.reset_rally_stall(gs)
                        ActionSystem.flip_initiative(gs)

            case AssaultAction():
                result = AssaultSystem.assault(gs, action.unit_id, action.target_id)
                if not isinstance(result, InvalidAction):
                    if (
                        result.outcome == AssaultOutcomes.FAIL
                        or FireOutcomes.SUPPRESS in result.reactive_fire_outcomes
                        or FireOutcomes.KILL in result.reactive_fire_outcomes
                    ):
                        ObjectiveSystem.reset_rally_stall(gs)
                        ActionSystem.flip_initiative(gs)

            case RallyAction():
                result = CommandSystem.rally(gs, action.unit_id)
                # TODO: have it flip initiative only when is success.
                ActionSystem.flip_initiative(gs)

        return result

    @staticmethod
    def is_legal(
        gs: GameState,
        action: Action,
    ) -> bool:
        """Checks whether an action is legal."""
        if not ActionSystem.has_initiative(gs, action.unit_id):
            return False

        match action:
            case MoveAction() | PivotAction():
                invalid_reason = MoveSystem.validate_move(
                    gs=gs,
                    unit_id=action.unit_id,
                    to=action.to,
                )
            case FireAction():
                invalid_reason = FireSystem.validate_fire_actors(
                    gs=gs,
                    attacker_id=action.unit_id,
                    target_id=action.target_id,
                )
            case AssaultAction():
                invalid_reason = AssaultSystem.validate_assault_action(
                    gs=gs,
                    attacker_id=action.unit_id,
                    target_id=action.target_id,
                )
                if invalid_reason == None:
                    target_transform = gs.get_component(action.target_id, Transform)
                    invalid_reason = MoveSystem.validate_move(
                        gs=gs,
                        unit_id=action.unit_id,
                        to=target_transform.position,
                    )
            case RallyAction():
                invalid_reason = None

        return not isinstance(invalid_reason, InvalidAction)

    @staticmethod
    def flip_initiative(
        gs: GameState,
    ) -> None:
        """Flips the current initiative to the opposing faction."""
        for _, initiative in gs.query(InitiativeState):
            match initiative.faction:
                case InitiativeState.Faction.RED:
                    initiative.faction = InitiativeState.Faction.BLUE
                case InitiativeState.Faction.BLUE:
                    initiative.faction = InitiativeState.Faction.RED

    @staticmethod
    def set_initiative(
        gs: GameState,
        faction: InitiativeState.Faction,
    ) -> None:
        """Sets the given faction to have the initiative."""
        for _, initiative_state in gs.query(InitiativeState):
            initiative_state.faction = faction

    @staticmethod
    def has_initiative(
        gs: GameState,
        unit_id: UUID,
    ) -> bool:
        """Check whether the unit's faction has initiative."""
        unit = gs.get_component(unit_id, CombatUnit)
        return unit.faction == ActionSystem.get_initiative(gs)

    @staticmethod
    def get_initiative(
        gs: GameState,
    ) -> InitiativeState.Faction:
        """Get the faction that has the current initiative."""
        for _, faction in gs.query(InitiativeState):
            return faction.faction
        raise Exception("InitiativeState component not found")
