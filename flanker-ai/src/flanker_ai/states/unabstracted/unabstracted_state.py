import random
from copy import deepcopy
from typing import Any, Sequence, override

from flanker_ai.actions import (
    Action,
    AssaultAction,
    FireAction,
    MoveAction,
    PivotAction,
)
from flanker_ai.components import AiStallCountComponent
from flanker_ai.i_representation_state import IRepresentationState
from flanker_ai.states.unabstracted.ai_branching_system import AiBranchingSystem
from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    AssaultControls,
    CombatUnit,
    InitiativeState,
    TerrainFeature,
    Transform,
)
from flanker_core.models.outcomes import AssaultOutcomes, InvalidAction
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.assault_system import AssaultSystem
from flanker_core.systems.fire_system import FireSystem
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.move_system import MoveSystem
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
    def copy(self) -> "UnabstractedState":
        branching_system = self._gs.get(AiBranchingSystem)
        new_gs = branching_system.copy(self._gs)
        return UnabstractedState(new_gs)

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
        move_system = self._gs.get(MoveSystem)
        assault_system = self._gs.get(AssaultSystem)
        fire_system = self._gs.get(FireSystem)
        branching_system = self._gs.get(AiBranchingSystem)

        # Prepare a list of configured branches
        branches: list[tuple[float, GameState]]
        match action:
            case MoveAction():
                branches = branching_system.get_reactive_fire_branches(
                    gs=self._gs,
                    unit_id=action.unit_id,
                    move_to=action.to,
                    is_deterministic=True,
                )
            case PivotAction():
                transform = self._gs.get_component(action.unit_id, Transform)
                branches = branching_system.get_reactive_fire_branches(
                    gs=self._gs,
                    unit_id=action.unit_id,
                    move_to=transform.position,
                    is_deterministic=True,
                )
            case AssaultAction():
                target_transform = self._gs.get_component(action.target_id, Transform)
                branches = branching_system.get_reactive_fire_branches(
                    gs=self._gs,
                    unit_id=action.unit_id,
                    move_to=target_transform.position,
                    is_deterministic=True,
                )
                for _, new_state in branches:
                    assault_controls = new_state.get_component(
                        action.unit_id, AssaultControls
                    )
                    assault_controls.override = AssaultOutcomes.SUCCESS
            case FireAction():
                branches = branching_system.get_fire_branches(
                    gs=self._gs,
                    unit_id=action.unit_id,
                )

        # Perform the actions
        waypoints_state_branches: list[tuple[float, UnabstractedState]] = []
        for probability, new_state in branches:
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

            new_branch = UnabstractedState(new_state)
            waypoints_state_branches.append((probability, new_branch))
        return waypoints_state_branches

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
        self._gs.register(AiBranchingSystem)

    def deabstract_action(self, action: Action, gs: GameState) -> Action:
        return action
