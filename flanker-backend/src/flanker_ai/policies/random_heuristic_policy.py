import random

from flanker_ai.i_policy import IPolicy
from flanker_ai.i_representation_state import IRepresentationState
from flanker_ai.policies.search_log_models import RandomHeuristicLog
from flanker_core.models.actions import (
    Action,
    AssaultAction,
    FireAction,
    MoveAction,
    PivotAction,
)


class RandomHeuristicPolicy(IPolicy[Action, RandomHeuristicLog]):
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
    ) -> tuple[Action | None, RandomHeuristicLog]:

        winner = rs.get_winner()
        if winner is not None:
            return None, RandomHeuristicLog(
                faction=rs.get_initiative(),
                actions_length=0,
            )

        actions = list(rs.get_actions(is_legal_only=False))
        if not actions:
            return None, RandomHeuristicLog(
                faction=rs.get_initiative(),
                actions_length=0,
            )

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
        random.shuffle(fire_actions)
        for action in fire_actions:
            if rs.is_legal(action):
                return action, RandomHeuristicLog(
                    faction=rs.get_initiative(),
                    actions_length=len(fire_actions),
                )

        # If any move actions are valid, perform it last
        random.shuffle(move_actions)
        for action in move_actions:
            if rs.is_legal(action):
                return action, RandomHeuristicLog(
                    faction=rs.get_initiative(),
                    actions_length=len(move_actions),
                )

        return None, RandomHeuristicLog(
            faction=rs.get_initiative(),
            actions_length=0,
        )
