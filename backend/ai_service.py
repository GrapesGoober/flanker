from backend import ActionService
from backend.action_service import AssaultActionRequest
from backend.models import FireActionRequest, MoveActionRequest
from core.components import InitiativeState
from core.initiative_system import InitiativeSystem
from core.gamestate import GameState


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
    def get_moves(gs: GameState) -> list[MoveActionRequest | FireActionRequest | AssaultActionRequest]:
        ...

    @staticmethod
    def evaluate(gs: GameState) -> float: ...

    @staticmethod
    def play_minimax(
        gs: GameState,
        depth: int,
        is_maximizing: bool = True,
    ) -> float:
        if depth == 0 or len(AiService.get_moves(gs)) == 0:
            return AiService.evaluate(gs)

        if is_maximizing:
            best_score = float("-inf")
            for move in AiService.get_moves(gs):
                new_gs = gs.copy()
                ActionService.perform_action(gs, move)
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
                ActionService.perform_action(gs, move)
                score = AiService.play_minimax(
                    new_gs,
                    depth - 1,
                    True,
                )
                best_score = min(best_score, score)
            return best_score
