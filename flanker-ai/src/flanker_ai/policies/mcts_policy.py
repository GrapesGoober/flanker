from __future__ import annotations

import math
from dataclasses import dataclass

from flanker_ai.i_policy import IPolicy
from flanker_ai.i_representation_state import IRepresentationState
from flanker_core.models.components import InitiativeState

MAXIMIZING_FACTION = InitiativeState.Faction.BLUE


@dataclass
class _MctsTreeNode[TAction]:
    state: IRepresentationState[TAction]
    parent: "_MctsTreeNode[TAction] | None"

    children: list["_MctsTreeNode[TAction]"]
    unexpanded_actions: list[TAction]  # All actions, some are illegal.

    visits: int
    value: float

    action: TAction | None


class MctsPolicy[TAction](IPolicy[TAction]):

    def __init__(self, max_iterations: int) -> None:
        self._max_iterations = max_iterations

    def get_action(
        self,
        rs: IRepresentationState[TAction],
    ) -> tuple[TAction | None, int]:
        root = _MctsTreeNode(
            state=rs,
            parent=None,
            children=[],
            unexpanded_actions=list(rs.get_actions()),
            visits=0,
            value=0,
            action=None,
        )

        # Expand the game tree. MCTS is stop-any-time, so run
        # until _max_iterations to stop, as deep as it needs.
        for _ in range(self._max_iterations):

            # Choose a leaf node with best UCT, and expand its leaves
            leaf = self._select_child_best_uct(root)
            child = self._expand(leaf)
            value = self._simulate(child)

            # Back propagate each node
            node: _MctsTreeNode[TAction] | None = child
            while node is not None:
                node.visits += 1
                node.value += value
                node = node.parent

        # No valid actions at this root
        if not root.children:
            return None, 0

        # Choose the root's best action to perform
        best = max(root.children, key=lambda c: c.visits)
        return best.action, 0

    def _select_child_best_uct(
        self,
        node: _MctsTreeNode[TAction],
    ) -> _MctsTreeNode[TAction]:
        """Search node's children with max UCT."""
        while (
            node.state.get_winner() == None
            and not node.unexpanded_actions
            and node.children
        ):
            assert node.children != None

            log_parent = math.log(node.visits)

            def uct(child: _MctsTreeNode[TAction]) -> float:
                if child.visits == 0:
                    return float("inf")

                exploitation = child.value / child.visits
                exploration = math.sqrt(2 * log_parent / child.visits)
                return exploitation + exploration

            node = max(node.children, key=uct)

        return node

    def _expand(
        self,
        node: _MctsTreeNode[TAction],
    ) -> _MctsTreeNode[TAction]:
        """
        Use any unexpanded action from node and expand it into a new child.
        """

        # Ignore expansion if terminal or if no expandable actions left.
        if node.state.get_winner() != None:
            return node
        if node.unexpanded_actions == []:
            return node

        # Some actions are illegal. Need to use a legal action.
        # Find the first legal action and its resulting state
        legal_action: TAction | None = None
        child_state: IRepresentationState[TAction] | None = None
        while node.unexpanded_actions:
            legal_action = node.unexpanded_actions.pop()
            child_state = node.state.get_one_branch(legal_action)
            if child_state is not None and legal_action is not None:
                break  # Found it!

        # No expandable legal action found
        if child_state is None or legal_action is None:
            return node

        child = _MctsTreeNode(
            state=child_state,
            parent=node,
            children=[],
            action=legal_action,
            unexpanded_actions=list(child_state.get_actions()),
            value=0,
            visits=0,
        )
        node.children.append(child)
        return child

    def _simulate(
        self,
        node: _MctsTreeNode[TAction],
    ) -> float:
        # TODO: Run a rollout until terminal and return reward from
        # MAXIMIZING_FACTION's perspective. I'm using heuristic score
        # for now. Configurable alternatives are possible.
        return node.state.get_score(MAXIMIZING_FACTION)
