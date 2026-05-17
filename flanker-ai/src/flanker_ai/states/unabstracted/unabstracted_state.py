import random
from copy import deepcopy
from typing import Sequence, override

from flanker_ai.actions import Action, AssaultAction, FireAction, MoveAction
from flanker_ai.components import AiStallCountComponent
from flanker_ai.i_representation_state import IRepresentationState
from flanker_ai.states.common.ai_branch_abstraction_service import (
    AiBranchAbstractionService,
)
from flanker_ai.states.common.ai_branching_service import AiBranchingService
from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    CombatUnit,
    InitiativeState,
    TerrainFeature,
    Transform,
)
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.objective_system import ObjectiveSystem
from flanker_core.utils.linear_transform import LinearTransform

_MAX_STALL_LIMIT = 5


class UnabstractedState(IRepresentationState[Action]):
    def __init__(self, gs: GameState) -> None:
        self._gs = gs
        boundary_vertices: list[Vec2] = []
        mask = TerrainFeature.Flag.BOUNDARY
        for _, terrain, transform in gs.query(TerrainFeature, Transform):
            if terrain.flag & mask:
                boundary_vertices = LinearTransform.apply(
                    terrain.vertices,
                    transform,
                )
                if terrain.is_closed_loop:
                    boundary_vertices.append(boundary_vertices[0])
        self.min_x = int(min(v.x for v in boundary_vertices))
        self.max_x = int(max(v.x for v in boundary_vertices))
        self.min_y = int(min(v.y for v in boundary_vertices))
        self.max_y = int(max(v.y for v in boundary_vertices))

    @override
    def get_score(self, maximizing_faction: InitiativeState.Faction) -> float:
        winner = self.get_winner()
        if winner is not None:
            if winner == maximizing_faction:
                return 10000
            else:
                return -10000

        score = 0.0
        for _, combat_unit in self._gs.query(CombatUnit):
            value = 0
            match combat_unit.status:
                case CombatUnit.Status.ACTIVE:
                    value = 3
                case CombatUnit.Status.PINNED:
                    value = 2
                case CombatUnit.Status.SUPPRESSED:
                    value = 1

            if combat_unit.faction == maximizing_faction:
                score += value
            else:
                score -= value
        return score

    @override
    def get_actions(self) -> Sequence[Action]:
        # Generate an action for each combat unit
        actions: list[Action] = []
        for unit_id, unit in self._gs.query(CombatUnit):
            if unit.faction == self.get_initiative():
                pos = self._gs.get_component(unit_id, Transform).position
                actions.append(
                    MoveAction(
                        unit_id=unit_id,
                        to=pos,
                    )
                )
                for _ in range(10):
                    rand_x = random.randrange(self.min_x, self.max_x)
                    rand_y = random.randrange(self.min_y, self.max_y)
                    vec = Vec2(rand_x, rand_y)
                    actions.append(
                        MoveAction(
                            unit_id=unit_id,
                            to=vec,
                        )
                    )

                # Fire and Assault actions for all permutations
                for target_id, target in self._gs.query(CombatUnit):
                    if target.faction != self.get_initiative():
                        actions.append(
                            AssaultAction(
                                unit_id=unit_id,
                                target_id=target_id,
                            )
                        )
                        actions.append(
                            FireAction(
                                unit_id=unit_id,
                                target_id=target_id,
                            )
                        )

        return actions

    @override
    def get_branches(
        self,
        action: Action,
    ) -> list[tuple[float, "UnabstractedState"]]:
        branches = AiBranchingService.get_action_branches(
            self._gs, action, is_deterministic=True
        )
        state_branches: list[tuple[float, UnabstractedState]] = []
        for probability, new_state in branches:
            state_branches.append((probability, UnabstractedState(new_state)))
        return state_branches

    @override
    def get_one_branch(
        self,
        action: Action,
    ) -> IRepresentationState[Action] | None:
        branches = AiBranchingService.get_action_branches(
            self._gs, action, is_deterministic=True
        )
        if branches == []:
            return None
        branch = AiBranchAbstractionService.get_one_approximate_branch(
            branches, action.unit_id
        )
        new_state = UnabstractedState(branch)
        return new_state

    @override
    def get_winner(self) -> InitiativeState.Faction | None:
        for faction, counter in self._get_stall_counter().items():
            if counter > _MAX_STALL_LIMIT:
                # mark faction as losing
                if faction == InitiativeState.Faction.BLUE:
                    return InitiativeState.Faction.RED
                elif faction == InitiativeState.Faction.RED:
                    return InitiativeState.Faction.BLUE

        objective_system = self._gs.get(ObjectiveSystem)
        return objective_system.get_winning_faction(self._gs)

    def _get_stall_counter(self) -> dict[InitiativeState.Faction, int]:
        if result := self._gs.query(AiStallCountComponent):
            _, stall_comp = result[0]
            return stall_comp.stall_counter
        else:
            raise ValueError(f"{AiStallCountComponent} missing for {self._gs}")

    @override
    def get_initiative(self) -> InitiativeState.Faction:
        initiative_system = self._gs.get(InitiativeSystem)
        return self._gs.get(initiative_system).get_initiative(self._gs)

    def update_state(self, gs: GameState) -> None:
        self._gs = deepcopy(gs)
        if self._gs.query(AiStallCountComponent) == []:
            self._gs.add_entity(AiStallCountComponent())
