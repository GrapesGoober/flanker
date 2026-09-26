import random

from flanker_ai.search_policies.i_search_policy import ISearchPolicy
from flanker_ai.search_policies.search_log_models import RandomSearchLog
from flanker_ai.search_states.i_search_state import ISearchState


class RandomPolicy[TAction](ISearchPolicy[TAction, RandomSearchLog]):
    """True random baseline policy."""

    def get_action(
        self,
        rs: ISearchState[TAction],
    ) -> tuple[TAction | None, RandomSearchLog]:

        winner = rs.get_winner()
        if winner is not None:
            return None, RandomSearchLog(
                actions_length=0,
            )

        actions = list(rs.get_actions(is_legal_only=False))
        if not actions:
            return None, RandomSearchLog(
                actions_length=0,
            )

        # Perform the first legal action
        random.shuffle(actions)
        for action in actions:
            if rs.is_legal(action):
                return action, RandomSearchLog(
                    actions_length=len(actions),
                )

        return None, RandomSearchLog(
            actions_length=0,
        )
