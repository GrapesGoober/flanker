from dataclasses import dataclass
from math import inf

from flanker_ai.i_policy import IPolicy
from flanker_ai.i_representation_state import IRepresentationState
from flanker_core.models.components import InitiativeState

MAXIMIZING_FACTION = InitiativeState.Faction.BLUE


@dataclass
class _MctsTreeNode[TAction]:
    state: IRepresentationState[TAction]
    parent: "_MctsTreeNode[TAction] | None"
    children: list[IRepresentationState[TAction]]


class MctsPolicy[TAction](IPolicy[TAction]):

    def __init__(self, depth: int) -> None:
        self._depth = depth

    def get_action(
        self,
        rs: IRepresentationState[TAction],
    ) -> tuple[TAction | None, int]:
        node = _MctsTreeNode(
            state=rs,
            parent=None,
            children=[],
        )
        _, action = self._search(node)
        return action, 0

    def _search(
        self,
        node: _MctsTreeNode[TAction],
        depth: int = 0,
    ) -> tuple[float, TAction | None]:

        # Just a placeholder minimax for now.
        state = node.state

        if depth >= self._depth or state.get_winner() != None:
            return state.get_score(MAXIMIZING_FACTION), None

        maximizing = state.get_initiative() == MAXIMIZING_FACTION

        best_score = -inf if maximizing else inf
        best_action: TAction | None = None

        for action in state.get_actions():
            child_state = state.get_one_branch(action)
            if child_state == None:
                continue
            child = _MctsTreeNode(
                state=child_state,
                parent=node,
                children=[],
            )

            score, _ = self._search(child, depth + 1)

            if maximizing:
                if score > best_score:
                    best_score = score
                    best_action = action
            else:
                if score < best_score:
                    best_score = score
                    best_action = action

        return best_score, best_action
