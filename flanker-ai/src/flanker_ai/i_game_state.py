from typing import Protocol, Sequence, runtime_checkable

from flanker_core.models.components import InitiativeState


@runtime_checkable
class IGameState[T](Protocol):
    """Interface for defining game state representation for AI"""

    def copy(self) -> "IGameState[T]":
        """Implements copying mechanism for Game State."""
        ...

    def get_score(self, maximizing_faction: InitiativeState.Faction) -> float:
        """Implements objective scoring for heuristic or terminal."""
        ...

    def get_actions(self) -> Sequence[T]:
        """Generates possible actions from the current state"""
        ...

    def get_branches(self, action: T) -> Sequence["IGameState[T]"]:
        """Generates possible brances from the current action."""
        ...

    def get_winner(self) -> InitiativeState.Faction | None:
        """Get the winning faction, if any"""
        ...

    def get_initiative(self) -> InitiativeState.Faction:
        """Get the current initiative holder."""
        ...
