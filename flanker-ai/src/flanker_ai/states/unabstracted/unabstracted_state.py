import random
from copy import deepcopy
from typing import Iterable, Literal, Sequence, override

from flanker_ai.actions import Action
from flanker_ai.components import AiStallCountComponent
from flanker_ai.i_representation_state import IRepresentationState
from flanker_ai.states.common.ai_action_service import AiActionService
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
from flanker_core.utils.intersect_getter import IntersectGetter
from flanker_core.utils.linear_transform import LinearTransform

_MAX_STALL_LIMIT = 5
_MOVE_SAMPLE_SIZE = 10


class UnabstractedState(IRepresentationState[Action]):
    def __init__(
        self,
        gs: GameState,
        move_candidates: list[Vec2] | Literal["Random"] = "Random",
    ) -> None:
        self._gs = gs
        if move_candidates == "Random":
            self.move_candidates = list(self.get_random_coordinates())
        else:
            self.move_candidates = move_candidates

    def get_random_coordinates(self) -> Iterable[Vec2]:
        boundary_vertices: list[Vec2] = []
        mask = TerrainFeature.Flag.BOUNDARY
        for _, terrain, transform in self._gs.query(TerrainFeature, Transform):
            if terrain.flag & mask:
                self.boundary_vertices = LinearTransform.apply(
                    terrain.vertices,
                    transform,
                )
                if terrain.is_closed_loop:
                    self.boundary_vertices.append(boundary_vertices[0])
        min_x = int(min(v.x for v in self.boundary_vertices))
        max_x = int(max(v.x for v in self.boundary_vertices))
        min_y = int(min(v.y for v in self.boundary_vertices))
        max_y = int(max(v.y for v in self.boundary_vertices))

        for _ in range(_MOVE_SAMPLE_SIZE):
            rand_x = random.randrange(min_x, max_x)
            rand_y = random.randrange(min_y, max_y)
            move_candidate = Vec2(rand_x, rand_y)
            if not IntersectGetter.is_inside(
                point=move_candidate,
                polygon=self.boundary_vertices,
            ):
                continue
            yield move_candidate

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
        return AiActionService.get_actions(
            gs=self._gs,
            initiative=self.get_initiative(),
            move_candidates=self.move_candidates,
        )

    @override
    def get_branches(
        self,
        action: Action,
    ) -> list[tuple[float, "UnabstractedState"]]:
        branches = AiBranchingService.get_action_branches(self._gs, action)
        state_branches: list[tuple[float, UnabstractedState]] = []
        for probability, new_state in branches:
            state_branches.append((probability, UnabstractedState(new_state)))
        return state_branches

    @override
    def get_one_branch(
        self,
        action: Action,
    ) -> IRepresentationState[Action] | None:
        branches = AiBranchingService.get_action_branches(self._gs, action)
        if branches == []:
            return None
        branch = AiBranchAbstractionService.pick_branch(branches, action)
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
