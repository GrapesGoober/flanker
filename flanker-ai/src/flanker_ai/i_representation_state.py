from typing import Protocol, Sequence, runtime_checkable

from flanker_core.gamestate import GameState
from flanker_core.models.components import InitiativeState


@runtime_checkable
class IRepresentationState[TAction](Protocol):
    """Interface for defining game state representation for AI"""

    def get_score(
        self,
        maximizing_faction: InitiativeState.Faction,
    ) -> float:
        """Implements objective scoring given a maximizer."""
        ...

    def get_actions(self) -> Sequence[TAction]:
        """Get possible actions from the current state"""
        ...

    def get_branches(
        self,
        action: TAction,
    ) -> Sequence[tuple[float, "IRepresentationState[TAction]"]]:
        """Get branches and their probability from the current action."""
        ...

    def get_one_branch(
        self,
        action: TAction,
    ) -> "IRepresentationState[TAction] | None":
        """Get one most likely branch from the current action."""
        ...

    def get_winner(self) -> InitiativeState.Faction | None:
        """Get the winning faction, if any"""
        ...

    def get_initiative(self) -> InitiativeState.Faction:
        """Get the current initiative holder."""
        ...

    def update_state(self, gs: GameState) -> None:
        """Update the state to match the original game state."""
        ...
