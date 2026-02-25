from typing import Protocol, Sequence, runtime_checkable

from flanker_core.models.components import InitiativeState


@runtime_checkable
class IGameState[TAction](Protocol):
    """Interface for defining game state representation for AI"""

    def copy(self) -> "IGameState[TAction]":
        """Implements copying mechanism for Game State."""
        ...

    def get_score(self, maximizing_faction: InitiativeState.Faction) -> float:
        """Implements objective scoring given a maximizer."""
        ...

    def get_actions(self) -> Sequence[TAction]:
        """Generates possible actions from the current state"""
        ...

    def get_branches(
        self, action: TAction
    ) -> Sequence[tuple[float, "IGameState[TAction]"]]:
        """Generate branches and their probability from the current action."""
        ...

    def get_deterministic_branch(
        self,
        action: TAction,
    ) -> "IGameState[TAction] | None":
        """Generates one most likely branch deterministically."""
        ...

    def get_winner(self) -> InitiativeState.Faction | None:
        """Get the winning faction, if any"""
        ...

    def get_initiative(self) -> InitiativeState.Faction:
        """Get the current initiative holder."""
        ...
