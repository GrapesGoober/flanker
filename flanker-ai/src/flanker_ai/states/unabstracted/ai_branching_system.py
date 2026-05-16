from itertools import product
from math import prod
from typing import Any, Literal
from uuid import UUID

from flanker_ai.actions import (
    Action,
    AssaultAction,
    FireAction,
    MoveAction,
    PivotAction,
)
from flanker_ai.components import AiStallCountComponent, InitiativeState
from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    AssaultControls,
    CombatUnit,
    EliminationObjective,
    FireControls,
    Transform,
)
from flanker_core.models.outcomes import AssaultOutcomes, FireOutcomes, InvalidAction
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.assault_system import AssaultSystem
from flanker_core.systems.fire_system import FireSystem
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.move_system import MoveSystem


class AiBranchingSystem:
    """
    AI specific system class responsible for generating branching states
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
    def _count_stall(
        gs: GameState,
        count: Literal["up"] | Literal["reset"],
    ) -> None:

        if entities := gs.query(AiStallCountComponent):
            _, stall_component = entities[0]
        else:
            gs.add_entity(stall_component := AiStallCountComponent())

        initiative_system = gs.get(InitiativeSystem)
        initiative = initiative_system.get_initiative(gs)
        match count:
            case "up":
                stall_component.stall_counter[initiative] += 1
            case "reset":
                stall_component.stall_counter[initiative] = 0

    @staticmethod
    def copy(gs: GameState) -> GameState:
        """Selectively copy the game state for mutating entities."""

        entities_to_copy: set[UUID] = set()
        for id, _ in gs.query(InitiativeState):
            entities_to_copy.add(id)
        for id, _ in gs.query(EliminationObjective):
            entities_to_copy.add(id)
        for id, _ in gs.query(CombatUnit):
            entities_to_copy.add(id)
        for id, _ in gs.query(AiStallCountComponent):
            entities_to_copy.add(id)
        return gs.selective_copy(list(entities_to_copy))

    @staticmethod
    def get_reactive_fire_branches(
        gs: GameState,
        unit_id: UUID,
        move_to: Vec2,
        is_deterministic: bool,
    ) -> list[tuple[float, GameState]]:
        """Get new game state branches configured with reactive fire overrides."""

        move_system = gs.get(MoveSystem)
        branching_system = gs.get(AiBranchingSystem)
        reactive_fire_candidates = move_system.get_interrupt_candidates(
            gs, unit_id, move_to
        )
        reactive_fire_ids = {
            uid for _, uuid_list in reactive_fire_candidates for uid in uuid_list
        }

        # No reactive fire found; this is garantee outcome
        if len(reactive_fire_ids) == 0:
            new_state = branching_system.copy(gs)
            branching_system._count_stall(new_state, "up")
            return [(1, new_state)]

        # Reactive fire found; configure all permutations
        permutations: list[tuple[float, dict[UUID, FireOutcomes]]]
        if is_deterministic:
            if len(reactive_fire_ids) == 1:
                outcomes = {next(iter(reactive_fire_ids)): FireOutcomes.PIN}
            else:
                # Enforce avoidance by having it assume
                # 2 reactive fires means SUPPRESS, and 3 means KILL
                outcomes = {
                    enemy_id: FireOutcomes.SUPPRESS for enemy_id in reactive_fire_ids
                }
                outcomes[next(iter(reactive_fire_ids))] = FireOutcomes.PIN
            permutations = [(1, outcomes)]
        else:
            permutations = branching_system.get_permutations(
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
            new_state = branching_system.copy(gs)
            branching_system._count_stall(new_state, count="reset")
            for firer_id, firer_outcome in unit_fire_outcomes.items():
                fire_controls = new_state.get_component(firer_id, FireControls)
                fire_controls.override = firer_outcome
            branching_states.append((probability, new_state))
        return branching_states

    @staticmethod
    def get_fire_branches(
        gs: GameState,
        unit_id: UUID,
        is_deterministic: bool,
    ) -> list[tuple[float, GameState]]:
        """Get new game state branches configured with active fire overrides."""
        branching_system = gs.get(AiBranchingSystem)

        permutations: list[tuple[float, dict[UUID, FireOutcomes]]]
        if is_deterministic:
            permutations = [(1, {unit_id: FireOutcomes.SUPPRESS})]
        else:
            permutations = branching_system.get_permutations(
                unit_ids={unit_id},
                outcome_probabilities={
                    # Make AI assume it's more likely to suppress
                    FireOutcomes.SUPPRESS: 0.6,
                    FireOutcomes.PIN: 0.4,
                },
            )

        branching_states: list[tuple[float, GameState]] = []
        for probability, outcomes in permutations:
            new_state = branching_system.copy(gs)
            branching_system._count_stall(new_state, count="reset")
            for id_to_override, outcome in outcomes.items():
                fire_controls = new_state.get_component(id_to_override, FireControls)
                fire_controls.override = outcome
            branching_states.append((probability, new_state))
        return branching_states

    @staticmethod
    def get_action_branches(
        gs: GameState, action: Action, is_deterministic: bool
    ) -> list[tuple[float, GameState]]:
        """
        Returns a list of branching states and their probabilities
        from a given action.
        """

        move_system = gs.get(MoveSystem)
        assault_system = gs.get(AssaultSystem)
        fire_system = gs.get(FireSystem)
        branching_system = gs.get(AiBranchingSystem)

        # Prepare a list of configured branches
        branches: list[tuple[float, GameState]]
        match action:
            case MoveAction():
                branches = branching_system.get_reactive_fire_branches(
                    gs=gs,
                    unit_id=action.unit_id,
                    move_to=action.to,
                    is_deterministic=is_deterministic,
                )
            case PivotAction():
                transform = gs.get_component(action.unit_id, Transform)
                branches = branching_system.get_reactive_fire_branches(
                    gs=gs,
                    unit_id=action.unit_id,
                    move_to=transform.position,
                    is_deterministic=is_deterministic,
                )
            case AssaultAction():
                target_transform = gs.get_component(action.target_id, Transform)
                target_unit = gs.get_component(action.target_id, CombatUnit)
                branches = branching_system.get_reactive_fire_branches(
                    gs=gs,
                    unit_id=action.unit_id,
                    move_to=target_transform.position,
                    is_deterministic=is_deterministic,
                )
                for _, new_state in branches:
                    assault_controls = new_state.get_component(
                        action.unit_id, AssaultControls
                    )
                    if target_unit.status == CombatUnit.Status.SUPPRESSED:
                        assault_controls.override = AssaultOutcomes.SUCCESS
                    else:
                        assault_controls.override = AssaultOutcomes.FAIL
            case FireAction():
                branches = branching_system.get_fire_branches(
                    gs=gs, unit_id=action.unit_id, is_deterministic=is_deterministic
                )

        # Perform the actions
        for _, new_state in branches:
            result: Any | InvalidAction
            match action:
                case MoveAction():
                    result = move_system.move(
                        gs=new_state,
                        unit_id=action.unit_id,
                        to=action.to,
                    )
                case PivotAction():
                    result = move_system.pivot(
                        gs=new_state,
                        unit_id=action.unit_id,
                        to=action.to,
                    )
                case AssaultAction():
                    result = assault_system.assault(
                        gs=new_state,
                        attacker_id=action.unit_id,
                        target_id=action.target_id,
                    )
                case FireAction():
                    result = fire_system.fire(
                        gs=new_state,
                        attacker_id=action.unit_id,
                        target_id=action.target_id,
                    )

            # Invalid action won't be performable.
            if isinstance(result, InvalidAction):
                return []

        return branches
