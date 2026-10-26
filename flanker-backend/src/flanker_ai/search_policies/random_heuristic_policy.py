import random
from dataclasses import dataclass

from flanker_ai.search_states.i_search_state import ISearchState
from flanker_core.models.actions import (
    Action,
    AssaultAction,
    FireAction,
    MoveAction,
    PivotAction,
    RallyAction,
)


@dataclass
class _RandomHeuristicLog:
    actions_length: int


class RandomHeuristicPolicy:
    """
    A Random-Heuristic search baseline policy.
    It prioritizes fire action first if legal, otherwise
    picks random moves, pivots, and assualt.
    """

    @staticmethod
    def get_action(
        rs: ISearchState[Action],
    ) -> tuple[Action | None, _RandomHeuristicLog]:

        winner = rs.get_winner()
        if winner is not None:
            return None, _RandomHeuristicLog(
                actions_length=0,
            )

        actions = list(rs.get_actions(is_legal_only=False))
        if not actions:
            return None, _RandomHeuristicLog(
                actions_length=0,
            )

        # Categorizes actions into candidate fire actions or move actions
        fire_actions: list[FireAction] = []
        move_actions: list[MoveAction | AssaultAction | PivotAction] = []
        rally_actions: list[RallyAction] = []
        for action in actions:
            match action:
                case FireAction():
                    fire_actions.append(action)
                case MoveAction() | AssaultAction() | PivotAction():
                    move_actions.append(action)
                case RallyAction():
                    rally_actions.append(action)

        # Have it randomly rally. This is to break up RH's aggressiveness.
        if random.randint(0, 1) == 0:
            random.shuffle(rally_actions)
            for action in rally_actions:
                if not rs.is_legal(action):
                    continue
                # Make sure that the rally won't straight up lose.
                branch = rs.get_one_branch(action)
                if branch == None:
                    continue
                if branch.get_winner() != rs.get_initiative():
                    continue
                return action, _RandomHeuristicLog(
                    actions_length=len(rally_actions),
                )

        # If any fire actions are valid, perform it first
        random.shuffle(fire_actions)
        for action in fire_actions:
            if not rs.is_legal(action):
                continue
            return action, _RandomHeuristicLog(
                actions_length=len(fire_actions),
            )

        # If it can't fire, but any move actions are valid, perform it
        random.shuffle(move_actions)
        for action in move_actions:
            if not rs.is_legal(action):
                continue
            return action, _RandomHeuristicLog(
                actions_length=len(move_actions),
            )

        # If no moves valid, try to rally what few units it has left
        random.shuffle(rally_actions)
        for action in rally_actions:
            if not rs.is_legal(action):
                continue
            return action, _RandomHeuristicLog(
                actions_length=len(rally_actions),
            )

        return None, _RandomHeuristicLog(
            actions_length=0,
        )
