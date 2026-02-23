from typing import Protocol, Sequence, runtime_checkable

from flanker_core.models.components import InitiativeState


@runtime_checkable
class IGameState(Protocol):
    """Protocol for defining game state representation for AI"""

    def copy(self) -> "IGameState":
        """Implements copying mechanism for Game State."""
        ...

    def get_score(self) -> float:
        """Implements objective scoring for heuristic or terminal."""
        ...

    def get_branches(self) -> Sequence["IGameState"]:
        """Generates possible branching from the current state."""
        ...

    def get_winner(self) -> InitiativeState.Faction | None:
        """Get the winning faction, if any"""
        ...
