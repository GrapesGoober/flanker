from dataclasses import replace
from itertools import product
from math import prod
from typing import Any
from uuid import UUID

from flanker_ai.actions import (
    Action,
    AssaultAction,
    FireAction,
    MoveAction,
    PivotAction,
)
from flanker_ai.components import InitiativeState
from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    AssaultControls,
    CombatUnit,
    EliminationWinCondition,
    FireControls,
    StallLoseCondition,
    Transform,
)
from flanker_core.models.outcomes import AssaultOutcomes, FireOutcomes, InvalidAction
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.action_system import ActionSystem
from flanker_core.systems.fire_system import FireSystem
from flanker_core.systems.move_system import MoveSystem


class AiBranchingService:
    """
    AI specific service class responsible for generating branching states
    and their probabilities given an action. This will configure permutations
    for each action type, copy the game state, and apply the actions.
    """

    @staticmethod
    def get_permutations[T](
        unit_ids: set[UUID],
        outcome_probabilities: dict[T, float],
    ) -> list[tuple[float, dict[UUID, T]]]:
        """Get a list of all event permutations T for each entity ID"""

        permutations: list[
            tuple[
                float,  # total probability of this permutation event
                dict[UUID, T],  # event (key=entity, value=outcome)
            ]
        ] = []

        # Assemble the probability and fire outcomes
        outcomes = list(outcome_probabilities.keys())
        for outcome_combo in product(outcomes, repeat=len(unit_ids)):
            probability = prod(
                outcome_probabilities[outcome] for outcome in outcome_combo
            )
            event = {
                unit_id: outcome for unit_id, outcome in zip(unit_ids, outcome_combo)
            }
            permutations.append((probability, event))
        return permutations

    @staticmethod
    def copy(gs: GameState) -> GameState:
        """Selectively copy the game state for mutating entities."""

        return gs.selective_copy(
            # Copy the combat units
            Transform,
            CombatUnit,
            FireControls,
            AssaultControls,
            # Copy the match-level data
            InitiativeState,
            EliminationWinCondition,
            StallLoseCondition,
            copy_method=replace,
        )

    @staticmethod
    def get_reactive_fire_branches(
        gs: GameState,
        unit_id: UUID,
        move_to: Vec2,
    ) -> list[tuple[float, GameState]]:
        """Get new game state branches configured with reactive fire overrides."""

        reactive_fire_candidates = MoveSystem.get_interrupt_candidates(
            gs, unit_id, move_to
        )
        reactive_fire_ids = {
            uid for _, uuid_list in reactive_fire_candidates for uid in uuid_list
        }

        if len(reactive_fire_ids) == 0:
            new_state = AiBranchingService.copy(gs)
            return [(1, new_state)]

        # Reactive fire found; configure all permutations
        permutations: list[tuple[float, dict[UUID, FireOutcomes]]]
        permutations = AiBranchingService.get_permutations(
            unit_ids=reactive_fire_ids,
            outcome_probabilities={
                FireOutcomes.PIN: 0.6,
                FireOutcomes.SUPPRESS: 0.4,
            },
        )
        if len(permutations) == 0:
            raise Exception("Permutations are empty, something went wrong!")

        # Permutation configured; create branches
        branching_states: list[tuple[float, GameState]] = []
        for probability, unit_fire_outcomes in permutations:
            new_state = AiBranchingService.copy(gs)
            for firer_id, firer_outcome in unit_fire_outcomes.items():
                fire_controls = new_state.get_component(firer_id, FireControls)
                fire_controls.override = firer_outcome
            branching_states.append((probability, new_state))
        return branching_states

    @staticmethod
    def get_fire_branches(
        gs: GameState,
        unit_id: UUID,
    ) -> list[tuple[float, GameState]]:
        """Get new game state branches configured with active fire overrides."""

        permutations: list[tuple[float, dict[UUID, FireOutcomes]]]
        permutations = AiBranchingService.get_permutations(
            unit_ids={unit_id},
            outcome_probabilities={
                # Make AI assume it's more likely to suppress
                FireOutcomes.SUPPRESS: 0.6,
                FireOutcomes.PIN: 0.4,
            },
        )

        branching_states: list[tuple[float, GameState]] = []
        for probability, outcomes in permutations:
            new_state = AiBranchingService.copy(gs)
            for id_to_override, outcome in outcomes.items():
                fire_controls = new_state.get_component(id_to_override, FireControls)
                fire_controls.override = outcome
            branching_states.append((probability, new_state))
        return branching_states

    @staticmethod
    def get_assault_branches(
        gs: GameState,
        unit_id: UUID,
        target_id: UUID,
    ) -> list[tuple[float, GameState]]:
        target_transform = gs.get_component(target_id, Transform)
        branches = AiBranchingService.get_reactive_fire_branches(
            gs=gs,
            unit_id=unit_id,
            move_to=target_transform.position,
        )
        for _, new_state in branches:
            assault_controls = new_state.get_component(unit_id, AssaultControls)
            if FireSystem.get_status(gs, target_id) == CombatUnit.Status.SUPPRESSED:
                assault_controls.override = AssaultOutcomes.SUCCESS
            else:
                assault_controls.override = AssaultOutcomes.FAIL
        return branches

    @staticmethod
    def get_action_branches(
        gs: GameState, action: Action
    ) -> list[tuple[float, GameState]]:
        """
        Returns a list of branching states and their probabilities
        from a given action.
        """
        # Prepare a list of configured branches
        branches: list[tuple[float, GameState]]
        match action:
            case MoveAction():
                branches = AiBranchingService.get_reactive_fire_branches(
                    gs=gs,
                    unit_id=action.unit_id,
                    move_to=action.to,
                )
            case PivotAction():
                transform = gs.get_component(action.unit_id, Transform)
                branches = AiBranchingService.get_reactive_fire_branches(
                    gs=gs,
                    unit_id=action.unit_id,
                    move_to=transform.position,
                )
            case AssaultAction():
                branches = AiBranchingService.get_assault_branches(
                    gs=gs,
                    unit_id=action.unit_id,
                    target_id=action.target_id,
                )
            case FireAction():
                branches = AiBranchingService.get_fire_branches(
                    gs=gs,
                    unit_id=action.unit_id,
                )

        # Perform the actions
        for _, new_state in branches:
            result: Any | InvalidAction
            result = ActionSystem.perform(new_state, action)
            # Invalid action won't be performable.
            if isinstance(result, InvalidAction):
                return []

        return branches
