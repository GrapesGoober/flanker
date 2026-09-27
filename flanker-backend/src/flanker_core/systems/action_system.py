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
)
from flanker_core.models.components import (
    CombatUnit,
    FireControls,
    InitiativeState,
    Transform,
)
from flanker_core.models.outcomes import (
    AssaultOutcomes,
    FireOutcomes,
    InvalidAction,
)
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

        if not ActionSystem.has_initiative(gs, action.unit_id):
            return InvalidAction.NO_INITIATIVE

        match action:
            case MoveAction():
                result = MoveSystem.move(gs, action.unit_id, action.to)
                if not isinstance(result, InvalidAction):
                    if {
                        FireOutcomes.SUPPRESS,
                        FireOutcomes.KILL,
                    } & set(result.reactive_fire_outcomes):
                        ActionSystem.flip_initiative(gs)

            case PivotAction():
                result = MoveSystem.pivot(gs, action.unit_id, action.to)
                if not isinstance(result, InvalidAction):
                    if {
                        FireOutcomes.SUPPRESS,
                        FireOutcomes.KILL,
                    } & set(result.reactive_fire_outcomes):
                        ActionSystem.flip_initiative(gs)

            case FireAction():
                result = FireSystem.fire(gs, action.unit_id, action.target_id)
                if not isinstance(result, InvalidAction):
                    if result.outcome in (FireOutcomes.MISS, FireOutcomes.PIN):
                        ActionSystem.flip_initiative(gs)

            case AssaultAction():
                result = AssaultSystem.assault(gs, action.unit_id, action.target_id)
                if not isinstance(result, InvalidAction):
                    if {
                        FireOutcomes.SUPPRESS,
                        FireOutcomes.KILL,
                    } & set(result.reactive_fire_outcomes):
                        ActionSystem.flip_initiative(gs)
                    if result.outcome == AssaultOutcomes.FAIL:
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
        return not isinstance(invalid_reason, InvalidAction)

    @staticmethod
    def flip_initiative(gs: GameState) -> None:
        """Sets the current initiative to the opposing faction."""
        for _, initiative in gs.query(InitiativeState):
            if initiative.faction == InitiativeState.Faction.RED:
                initiative.faction = InitiativeState.Faction.BLUE
            initiative.faction = InitiativeState.Faction.RED
        ActionSystem._update_unit_status(gs)

    @staticmethod
    def set_initiative(gs: GameState, faction: InitiativeState.Faction) -> None:
        """Sets the given faction to have the initiative."""
        for _, initiative_state in gs.query(InitiativeState):
            initiative_state.faction = faction
        ActionSystem._update_unit_status(gs)

    @staticmethod
    def has_initiative(gs: GameState, unit_id: UUID) -> bool:
        """Check whether the unit's faction has initiative."""
        unit = gs.get_component(unit_id, CombatUnit)
        return unit.faction == ActionSystem.get_initiative(gs)

    @staticmethod
    def get_initiative(gs: GameState) -> InitiativeState.Faction:
        """Get the faction that has the current initiative."""
        for _, faction in gs.query(InitiativeState):
            return faction.faction
        raise Exception("InitiativeState component not found")

    @staticmethod
    def _update_unit_status(
        gs: GameState,
    ) -> None:
        """Updates unit status of combat units from fire effects."""

        for unit_id, unit in gs.query(CombatUnit):
            if unit.faction != ActionSystem.get_initiative(gs):
                continue

            # Start at ACTIVE, accumulate each fire effect.
            unit.status = CombatUnit.Status.ACTIVE
            for _, fire_controls in gs.query(FireControls):
                if fire_controls.firing_at == None:
                    continue
                fire_at_id, fire_effect = fire_controls.firing_at
                if fire_at_id != unit_id:
                    continue

                FireSystem.apply_fire_effect(
                    gs,
                    target_id=unit_id,
                    fire_effect=fire_effect,
                )
