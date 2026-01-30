import random
from itertools import count
from typing import Iterator

from flanker_ai.unabstracted.models import (
    ActionResult,
    AssaultAction,
    AssaultActionResult,
    FireAction,
    FireActionResult,
    MoveAction,
    MoveActionResult,
)
from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    CombatUnit,
    EliminationObjective,
    InitiativeState,
    Transform,
)
from flanker_core.models.outcomes import InvalidAction
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.assault_system import AssaultSystem
from flanker_core.systems.fire_system import FireSystem
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.move_system import MoveSystem


class TreeSearchPlayer:
    """Implements a basic unabstracted one-side tree search AI player."""

    @staticmethod
    def _get_actions(
        gs: GameState,
    ) -> list[MoveAction | FireAction | AssaultAction]:
        # Generate an action for each combat unit
        actions: list[MoveAction | FireAction | AssaultAction] = []
        for unit_id, unit in gs.query(CombatUnit):
            if unit.faction == InitiativeState.Faction.BLUE:
                # 10 random actions for each unit
                pos = gs.get_component(unit_id, Transform).position
                actions.append(
                    MoveAction(
                        unit_id=unit_id,
                        to=pos,
                    )
                )
                for _ in range(5):
                    rand_x = random.randrange(-50, 50)
                    rand_y = random.randrange(-50, 50)
                    vec = Vec2(rand_x, rand_y)
                    actions.append(
                        MoveAction(
                            unit_id=unit_id,
                            to=pos + vec,
                        )
                    )

                # Fire and Assault actions for all permutations
                for target_id, target in gs.query(CombatUnit):
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

    @staticmethod
    def _evaluate(gs: GameState) -> float:
        score: float = 0.0
        for _, unit in gs.query(CombatUnit):
            if unit.faction == InitiativeState.Faction.BLUE:
                match unit.status:
                    case CombatUnit.Status.ACTIVE:
                        score += 3
                    case CombatUnit.Status.PINNED:
                        score += 2
                    case CombatUnit.Status.SUPPRESSED:
                        score += 1
            else:
                match unit.status:
                    case CombatUnit.Status.ACTIVE:
                        score -= 3
                    case CombatUnit.Status.PINNED:
                        score -= 2
                    case CombatUnit.Status.SUPPRESSED:
                        score -= 1
        return score

    @staticmethod
    def play_minimax(
        gs: GameState,
        depth: int,
        iter_counter: Iterator[int] | None = None,
    ) -> tuple[float, list[ActionResult]]:
        if depth == 0 or len(TreeSearchPlayer._get_actions(gs)) == 0:
            return TreeSearchPlayer._evaluate(gs), []

        best_score = float("-inf")
        best_result: list[ActionResult] = []
        deep_copy_entities = TreeSearchPlayer.get_deep_copy_entities(gs)
        for action in TreeSearchPlayer._get_actions(gs):
            new_gs = gs.selective_copy(deep_copy_entities)
            result = TreeSearchPlayer.perform_action(new_gs, action)
            if isinstance(result, InvalidAction):
                continue
            # Due to large tree size, I don't want to implement a "min" state
            # So have the opponent just do nothing (pass on the turn)
            InitiativeSystem.set_initiative(gs, InitiativeState.Faction.BLUE)
            if not iter_counter:
                iter_counter = count(0)
            iter = next(iter_counter)
            if iter % 100 == 0:
                print(f"Evaluated {iter=}")
            score, results = TreeSearchPlayer.play_minimax(
                new_gs,
                depth - 1,
                iter_counter=iter_counter,
            )
            if score > best_score:
                best_score = score
                best_result = [result] + results
        return best_score, best_result

    @staticmethod
    def perform_action(
        gs: GameState,
        action: MoveAction | FireAction | AssaultAction,
    ) -> ActionResult | InvalidAction:
        match action:
            case MoveAction():
                result = MoveSystem.move(gs, action.unit_id, action.to)
                if not isinstance(result, InvalidAction):
                    return MoveActionResult(
                        action=action,
                        result_gs=gs,
                        reactive_fire_outcome=result.reactive_fire_outcome,
                    )
            case FireAction():
                result = FireSystem.fire(gs, action.unit_id, action.target_id)
                if not isinstance(result, InvalidAction):
                    return FireActionResult(
                        action=action,
                        result_gs=gs,
                        outcome=result.outcome,
                    )
            case AssaultAction():
                result = AssaultSystem.assault(gs, action.unit_id, action.target_id)
                if not isinstance(result, InvalidAction):
                    return AssaultActionResult(
                        action=action,
                        result_gs=gs,
                        outcome=result.outcome,
                        reactive_fire_outcome=result.reactive_fire_outcome,
                    )
        return result

    @staticmethod
    def get_deep_copy_entities(gs: GameState) -> list[int]:
        mutable_entities: set[int] = set()
        for id, _ in gs.query(InitiativeState):
            mutable_entities.add(id)
        for id, _ in gs.query(EliminationObjective):
            mutable_entities.add(id)
        for id, _ in gs.query(CombatUnit):
            mutable_entities.add(id)
        return list(mutable_entities)
