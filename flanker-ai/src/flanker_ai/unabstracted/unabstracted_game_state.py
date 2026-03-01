import random
from typing import Sequence

from flanker_ai.i_game_state import IRepresentationState
from flanker_ai.actions import Action, AssaultAction, FireAction, MoveAction
from flanker_ai.waypoints.models import EliminationObjective
from flanker_ai.waypoints.waypoints_game_state import CombatUnit
from flanker_core.gamestate import GameState
from flanker_core.models.components import (
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
from flanker_core.systems.objective_system import ObjectiveSystem
from flanker_core.utils.linear_transform import LinearTransform


class UnabstractedGameState(IRepresentationState[Action]):
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

    def copy(self) -> "UnabstractedGameState":
        mutable_entities: set[int] = set()
        for id, _ in self._gs.query(InitiativeState):
            mutable_entities.add(id)
        for id, _ in self._gs.query(EliminationObjective):
            mutable_entities.add(id)
        for id, _ in self._gs.query(CombatUnit):
            mutable_entities.add(id)
        new_gs = self._gs.selective_copy(list(mutable_entities))
        return UnabstractedGameState(new_gs)

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
            if unit.faction == InitiativeState.Faction.BLUE:
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
                            to=pos + vec,
                        )
                    )

                # Fire and Assault actions for all permutations
                for target_id, target in self._gs.query(CombatUnit):
                    if target.faction == InitiativeState.Faction.RED:
                        if target.status == CombatUnit.Status.SUPPRESSED:
                            actions.append(
                                AssaultAction(
                                    unit_id=unit_id,
                                    target_id=target_id,
                                )
                            )
                        else:
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
    ) -> Sequence[tuple[float, "UnabstractedGameState"]]:
        branch = self.get_deterministic_branch(action)
        if branch == None:
            return []
        return [(1, branch)]

    def get_deterministic_branch(
        self, action: Action
    ) -> "UnabstractedGameState | None":
        new_gs = self.copy()._gs
        match action:
            case MoveAction():
                for _, fire_controls in new_gs.query(FireControls):
                    fire_controls.override = FireOutcomes.PIN
                result = MoveSystem.move(new_gs, action.unit_id, action.to)
            case FireAction():
                for _, fire_controls in new_gs.query(FireControls):
                    fire_controls.override = FireOutcomes.SUPPRESS
                result = FireSystem.fire(new_gs, action.unit_id, action.target_id)
            case AssaultAction():
                for _, fire_controls in new_gs.query(FireControls):
                    fire_controls.override = FireOutcomes.PIN
                result = AssaultSystem.assault(new_gs, action.unit_id, action.target_id)
        for _, fire_controls in new_gs.query(FireControls):
            fire_controls.override = None

        if isinstance(result, InvalidAction):
            return None
        return UnabstractedGameState(new_gs)

    def get_winner(self) -> InitiativeState.Faction | None:
        return ObjectiveSystem.get_winning_faction(self._gs)

    def get_initiative(self) -> InitiativeState.Faction:
        return InitiativeSystem.get_initiative(self._gs)

    def initialize_state(self, gs: GameState) -> None:
        self._gs = gs

    def update_state(self, gs: GameState) -> None:
        self._gs = gs

    def deabstract_action(self, action: Action, gs: GameState) -> Action:
        return action
