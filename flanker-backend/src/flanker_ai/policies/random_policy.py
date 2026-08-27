import random

from flanker_ai.i_policy import IPolicy
from flanker_ai.i_representation_state import IRepresentationState


class RandomPolicy[TAction](IPolicy[TAction]):
    """True random baseline policy."""

    def get_action(
        self,
        rs: IRepresentationState[TAction],
    ) -> tuple[TAction | None, int]:

        winner = rs.get_winner()
        if winner is not None:
            return None, 0

        actions = list(rs.get_actions(is_legal_only=False))
        if not actions:
            return None, 0

        # Perform the first legal action
        random.shuffle(actions)
        for action in actions:
            if rs.is_legal(action):
                return action, len(actions)

        return None, 0
