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

        actions = list(rs.get_actions())
        if not actions:
            return None, 0

        if actions != []:
            return random.choice(actions), len(actions)

        return None, 0
