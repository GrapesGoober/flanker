import random

from flanker_ai.i_policy import IPolicy
from flanker_ai.i_representation_state import IRepresentationState
from flanker_core.models.actions import (
    Action,
    AssaultAction,
    FireAction,
    MoveAction,
    PivotAction,
)


class RandomHeuristicPolicy(IPolicy[Action]):
    """
    Random Heuristic baseline agent.
    Logic:
    1. If an enemy is in LOF, Fire.
    2. Else, makes random move actions, assaults, or pivots.

    It searches through the representation and finds the action that
    best match the heuristic criteria.
    """

    def get_action(
        self,
        rs: IRepresentationState[Action],
    ) -> tuple[Action | None, int]:

        winner = rs.get_winner()
        if winner is not None:
            return None, 0

        actions = list(rs.get_actions())
        if not actions:
            return None, 0

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
        if fire_actions != []:
            return random.choice(fire_actions), len(fire_actions)

        # If any move actions are valid, perform it last
        if move_actions != []:
            return random.choice(move_actions), len(move_actions)

        return None, 0
