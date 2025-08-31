import random
from backend import ActionService
from backend.action_service import AssaultActionRequest
from backend.models import FireActionRequest, MoveActionRequest
from core.components import CombatUnit, InitiativeState, Transform
from core.initiative_system import InitiativeSystem
from core.gamestate import GameState
from copy import deepcopy

from core.utils.vec2 import Vec2

num_states: int = 0
num_depth: int = 0


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
    def get_moves(
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
                for _ in range(10):
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
                score += 1
            else:
                score -= 1
        return score

    @staticmethod
    def play_minimax(
        gs: GameState,
        depth: int,
        is_maximizing: bool = True,
    ) -> float:
        if depth == 0 or len(AiService.get_moves(gs)) == 0:
            return AiService.evaluate(gs)

        global num_depth
        if depth > num_depth:
            num_depth = depth
        global num_states

        if is_maximizing:
            best_score = float("-inf")
            for move in AiService.get_moves(gs):
                new_gs = deepcopy(gs)
                is_valid = ActionService.perform_action(new_gs, move)
                if not is_valid:
                    continue
                num_states += 1
                print(f"Evaluated {num_depth=} with {num_states}")
                score = AiService.play_minimax(
                    new_gs,
                    depth - 1,
                    False,
                )
                best_score = max(best_score, score)
            return best_score
        else:
            best_score = float("inf")
            for move in AiService.get_moves(gs):
                new_gs = deepcopy(gs)
                is_valid = ActionService.perform_action(new_gs, move)
                if not is_valid:
                    continue
                num_states += 1
                print(f"Evaluated {num_depth=} with {num_states}")
                score = AiService.play_minimax(
                    new_gs,
                    depth - 1,
                    True,
                )
                best_score = min(best_score, score)
            return best_score
