import random
from backend.action_service import AssaultActionRequest
from backend.combat_unit_service import CombatUnitService
from backend.models import (
    ActionLog,
    AssaultActionLog,
    AssaultActionResult,
    FireActionLog,
    FireActionResult,
    MoveActionLog,
    MoveActionResult,
)
from backend.models import (
    FireActionRequest,
    MoveActionRequest,
)
from core.action_models import (
    InvalidActionTypes,
)
from core.components import (
    CombatUnit,
    InitiativeState,
    Transform,
)
from core.systems.assault_system import AssaultSystem
from core.systems.fire_system import FireSystem
from core.systems.initiative_system import InitiativeSystem
from core.systems.move_system import MoveSystem
from core.gamestate import GameState
from copy import deepcopy

from core.utils.vec2 import Vec2

num_states: int = 0
num_depth: int = (
    0  # TODO: this is a useless metric as tree search is depth first search
)


class AiService:
    """Provides static methods for basic AI behavior."""

    @staticmethod
    def play(gs: GameState) -> None:
        """Perform a basic AI turn for the given faction."""
        # Assume that the AI plays RED
        faction = InitiativeState.Faction.RED
        if InitiativeSystem.get_initiative(gs) != faction:
            return

        # For now, pass on initiative without any actions
        InitiativeSystem.flip_initiative(gs)

    @staticmethod
    def get_actions(
        gs: GameState,
    ) -> list[MoveActionRequest | FireActionRequest | AssaultActionRequest]:
        # Generate an action for each combat unit
        actions: list[MoveActionRequest | FireActionRequest | AssaultActionRequest] = []
        for unit_id, unit in gs.query(CombatUnit):
            if unit.faction == InitiativeState.Faction.BLUE:
                # 10 random actions for each unit
                pos = gs.get_component(unit_id, Transform).position
                actions.append(
                    MoveActionRequest(
                        unit_id=unit_id,
                        to=pos,
                    )
                )
                for _ in range(5):
                    rand_x = random.randrange(-50, 50)
                    rand_y = random.randrange(-50, 50)
                    vec = Vec2(rand_x, rand_y)
                    actions.append(
                        MoveActionRequest(
                            unit_id=unit_id,
                            to=pos + vec,
                        )
                    )

                # Fire and Assault actions for all permutations
                for target_id, target in gs.query(CombatUnit):
                    if target.faction == InitiativeState.Faction.RED:
                        if target.status == CombatUnit.Status.SUPPRESSED:
                            actions.append(
                                AssaultActionRequest(
                                    unit_id=unit_id,
                                    target_id=target_id,
                                )
                            )
                        else:
                            actions.append(
                                FireActionRequest(
                                    unit_id=unit_id,
                                    target_id=target_id,
                                )
                            )

        return actions

    @staticmethod
    def evaluate(gs: GameState) -> float:
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
    ) -> tuple[float, list[ActionLog]]:
        if depth == 0 or len(AiService.get_actions(gs)) == 0:
            return AiService.evaluate(gs), []

        global num_depth
        if depth > num_depth:
            num_depth = depth
        global num_states

        best_score = float("-inf")
        best_logs: list[ActionLog] = []
        for action in AiService.get_actions(gs):
            new_gs = deepcopy(gs)
            log = AiService.perform_action(new_gs, action)
            if isinstance(log, InvalidActionTypes):
                continue
            num_states += 1
            AiService.play(new_gs)
            print(f"Evaluated {num_depth=} with {num_states=}")
            score, logs = AiService.play_minimax(
                new_gs,
                depth - 1,
            )
            if score > best_score:
                best_score = score
                best_logs = [log] + logs
        return best_score, best_logs

    @staticmethod
    def perform_action(
        gs: GameState,
        body: MoveActionRequest | FireActionRequest | AssaultActionRequest,
    ) -> ActionLog | InvalidActionTypes:
        if isinstance(body, MoveActionRequest):
            result = MoveSystem.move(gs, body.unit_id, body.to)
            if not isinstance(result, InvalidActionTypes):
                return MoveActionLog(
                    body=body,
                    result=MoveActionResult(
                        reactive_fire_outcome=result.reactive_fire_outcome
                    ),
                    unit_state=CombatUnitService.get_units(gs),
                )
        elif isinstance(body, FireActionRequest):
            result = FireSystem.fire(gs, body.unit_id, body.target_id)
            if not isinstance(result, InvalidActionTypes):
                return FireActionLog(
                    body=body,
                    result=FireActionResult(outcome=result.outcome),
                    unit_state=CombatUnitService.get_units(gs),
                )
        else:
            result = AssaultSystem.assault(gs, body.unit_id, body.target_id)
            if not isinstance(result, InvalidActionTypes):
                return AssaultActionLog(
                    body=body,
                    result=AssaultActionResult(
                        outcome=result.outcome,
                        reactive_fire_outcome=result.reactive_fire_outcome,
                    ),
                    unit_state=CombatUnitService.get_units(gs),
                )
        return result
