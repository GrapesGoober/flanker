import random

from flanker_ai.i_policy import IPolicy
from flanker_ai.i_representation_state import IRepresentationState


class RandomPolicy[TAction](IPolicy[TAction]):
    """
    True random policy. Picks the any random legal action to perform.
    """

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

        # Randomly pick any action until a legal one is found
        result_state: IRepresentationState[TAction] | None = None
        while actions != []:
            action = actions.pop(random.randrange(len(actions)))
            # Valid actions would have not-none result
            result_state = rs.get_one_branch(action)
            if result_state == None:
                return result_state, 0
        return None, 0
