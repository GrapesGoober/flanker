import random
from typing import Callable, Sequence

from flanker_ai.actions import (
    Action,
    AssaultAction,
    FireAction,
    MoveAction,
    PivotAction,
)
from flanker_ai.i_policy import IPolicy
from flanker_ai.i_representation_state import IRepresentationState
from flanker_core.gamestate import GameState


class RandomHeuristicPolicy(IPolicy[Action]):
    """
    Random Heuristic baseline agent.
    Logic:
    1. If an enemy is in LOF, Fire.
    2. Else, makes random move actions, assaults, or pivots.

    It searches through the representation and finds the action that
    best match the heuristic criteria.
    """

    def __init__(
        self,
        gs: GameState,  # Needed for deabstraction
    ) -> None:
        self._gs = gs

    def get_action_sequence(
        self,
        rs: IRepresentationState[Action],
        callback: Callable[[], None] | None = None,
    ) -> Sequence[Action]:

        winner = rs.get_winner()
        if winner is not None:
            return []

        actions = list(rs.get_actions())
        if not actions:
            return []

        # Categorizes actions into candidate fire actions or move actions
        fire_actions: list[Action] = []
        move_actions: list[Action] = []
        for action in actions:
            match action:
                case FireAction():
                    fire_actions.append(action)
                case MoveAction() | AssaultAction() | PivotAction():
                    move_actions.append(action)

        # If any fire actions are valid, perform it first
        action = self._pick_valid_action(rs, fire_actions)
        if action is not None:
            return [action]

        # If any move actions are valid, perform it last
        action = self._pick_valid_action(rs, move_actions)
        if action is not None:
            return [action]

        # No valid action
        return []

    def _pick_valid_action(
        self,
        rs: IRepresentationState[Action],
        candidates: list[Action],
    ) -> Action | None:
        """Randomly pick a valid action."""
        remaining = candidates.copy()
        while remaining:
            action = random.choice(remaining)
            remaining.remove(action)

            branches = rs.get_branches(action)
            if branches == []:
                continue  # Invalid action has no branching
            _, branch = max(branches, key=lambda b: b[0])

            # Reject losing actions
            if branch.get_winner() not in [None, rs.get_initiative()]:
                continue

            return action

        return None
