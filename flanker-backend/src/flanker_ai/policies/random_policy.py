import random

from flanker_ai.i_policy import IPolicy
from flanker_ai.i_representation_state import IRepresentationState
from flanker_ai.policies.search_log_models import RandomSearchLog


class RandomPolicy[TAction](IPolicy[TAction, RandomSearchLog]):
    """True random baseline policy."""

    def get_action(
        self,
        rs: IRepresentationState[TAction],
    ) -> tuple[TAction | None, RandomSearchLog]:

        winner = rs.get_winner()
        if winner is not None:
            return None, RandomSearchLog(
                faction=rs.get_initiative(),
                actions_length=0,
            )

        actions = list(rs.get_actions(is_legal_only=False))
        if not actions:
            return None, RandomSearchLog(
                faction=rs.get_initiative(),
                actions_length=0,
            )

        # Perform the first legal action
        random.shuffle(actions)
        for action in actions:
            if rs.is_legal(action):
                return action, RandomSearchLog(
                    faction=rs.get_initiative(),
                    actions_length=len(actions),
                )

        return None, RandomSearchLog(
            faction=rs.get_initiative(),
            actions_length=0,
        )
