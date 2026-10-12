import random
from dataclasses import dataclass

from flanker_ai.search_states.i_search_state import ISearchState


@dataclass
class _RandomSearchLog:
    actions_length: int


class RandomPolicy[TAction]:
    """True random baseline policy."""

    @staticmethod
    def get_action(
        rs: ISearchState[TAction],
    ) -> tuple[TAction | None, _RandomSearchLog]:

        winner = rs.get_winner()
        if winner is not None:
            return None, _RandomSearchLog(
                actions_length=0,
            )

        actions = list(rs.get_actions(is_legal_only=False))
        if not actions:
            return None, _RandomSearchLog(
                actions_length=0,
            )

        # Perform the first legal action
        random.shuffle(actions)
        for action in actions:
            if rs.is_legal(action):
                return action, _RandomSearchLog(
                    actions_length=len(actions),
                )

        return None, _RandomSearchLog(
            actions_length=0,
        )
