import random
from copy import deepcopy
from typing import Sequence

from flanker_ai.actions import (
    Action,
    AssaultAction,
    FireAction,
    MoveAction,
    PivotAction,
)
from flanker_ai.components import AiStallCountComponent
from flanker_ai.i_representation_state import IRepresentationState
from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    CombatUnit,
    EliminationObjective,
    FireControls,
    InitiativeState,
    TerrainFeature,
    Transform,
)
from flanker_core.models.outcomes import FireOutcomes, InvalidAction
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.assault_system import AssaultSystem
from flanker_core.systems.fire_system import FireSystem
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.move_system import MoveSystem
from flanker_core.systems.pivot_system import PivotSystem
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

    def copy(self) -> "UnabstractedState":
        mutable_entities: set[int] = set()
        for id, _ in self._gs.query(InitiativeState):
            mutable_entities.add(id)
        for id, _ in self._gs.query(EliminationObjective):
            mutable_entities.add(id)
        for id, _ in self._gs.query(CombatUnit):
            mutable_entities.add(id)
        for id, _ in self._gs.query(AiStallCountComponent):
            mutable_entities.add(id)
        new_gs = self._gs.selective_copy(list(mutable_entities))
        return UnabstractedState(new_gs)

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
                # sample a few random wander moves
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

                # allow a handful of arbitrary pivots so the AI can change facing
                for _ in range(3):
                    actions.append(
                        PivotAction(
                            unit_id=unit_id,
                            degrees=random.random() * 360,
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

    def get_branches(
        self,
        action: Action,
    ) -> Sequence[tuple[float, "UnabstractedState"]]:
        branch = self.get_deterministic_branch(action)
        if branch == None:
            return []
        return [(1, branch)]

    def get_deterministic_branch(self, action: Action) -> "UnabstractedState | None":
        """Apply `action` to a copied state and return the successor or None."""
        new_state = self.copy()
        new_gs = new_state._gs
        # define a default so the variable is always bound for mypy/pylance
        result: object = InvalidAction
        match action:
            case MoveAction():
                initiative = InitiativeSystem.get_initiative(new_gs)
                for _, fire_controls in new_gs.query(FireControls):
                    fire_controls.override = FireOutcomes.PIN
                result = MoveSystem.move(new_gs, action.unit_id, action.to)
                if not isinstance(result, InvalidAction):
                    if result.reactive_fire_outcome == None:
                        self._get_stall_counter()[initiative] += 1
                    else:
                        self._get_stall_counter()[initiative] = 0
            case FireAction():
                initiative = InitiativeSystem.get_initiative(new_gs)
                self._get_stall_counter()[initiative] = 0
                for _, fire_controls in new_gs.query(FireControls):
                    fire_controls.override = FireOutcomes.SUPPRESS
                result = FireSystem.fire(new_gs, action.unit_id, action.target_id)
            case AssaultAction():
                initiative = InitiativeSystem.get_initiative(new_gs)
                self._get_stall_counter()[initiative] = 0
                for _, fire_controls in new_gs.query(FireControls):
                    fire_controls.override = FireOutcomes.PIN
                result = AssaultSystem.assault(new_gs, action.unit_id, action.target_id)
            case PivotAction():
                initiative = InitiativeSystem.get_initiative(new_gs)
                for _, fire_controls in new_gs.query(FireControls):
                    fire_controls.override = FireOutcomes.PIN
                result = PivotSystem.pivot(new_gs, action.unit_id, action.degrees)
                if not isinstance(result, InvalidAction):
                    # pivot is treated as a free move for stall counting
                    self._get_stall_counter()[initiative] += 1
            case _:
                # any other action type is illegal in this state
                result = InvalidAction
        for _, fire_controls in new_gs.query(FireControls):
            fire_controls.override = None

        if isinstance(result, InvalidAction):
            return None
        return UnabstractedState(new_gs)

    def get_winner(self) -> InitiativeState.Faction | None:
        for faction, counter in self._get_stall_counter().items():
            if counter > _MAX_STALL_LIMIT:
                # mark faction as losing
                if faction == InitiativeState.Faction.BLUE:
                    return InitiativeState.Faction.RED
                elif faction == InitiativeState.Faction.RED:
                    return InitiativeState.Faction.BLUE

        return ObjectiveSystem.get_winning_faction(self._gs)

    def _get_stall_counter(self) -> dict[InitiativeState.Faction, int]:
        if result := self._gs.query(AiStallCountComponent):
            _, stall_comp = result[0]
            return stall_comp.stall_counter
        else:
            raise ValueError(f"{AiStallCountComponent} missing for {self._gs}")

    def get_initiative(self) -> InitiativeState.Faction:
        return InitiativeSystem.get_initiative(self._gs)

    def get_transform(self, unit_id: int) -> Transform:
        """Convenience accessor for a unit's Transform component.

        This avoids external code reaching into the protected `_gs` attribute
        while still exposing required information for testing and scoring.
        """
        return self._gs.get_component(unit_id, Transform)

    def initialize_state(self, gs: GameState) -> None:
        self._gs = deepcopy(gs)
        if self._gs.query(AiStallCountComponent) == []:
            self._gs.add_entity(AiStallCountComponent())

    def update_state(self, gs: GameState) -> None:
        self._gs = deepcopy(gs)
        if self._gs.query(AiStallCountComponent) == []:
            self._gs.add_entity(AiStallCountComponent())

    def deabstract_action(self, action: Action, gs: GameState) -> Action:
        return action
