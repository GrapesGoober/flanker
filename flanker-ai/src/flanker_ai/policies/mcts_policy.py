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
    unexpanded_actions: list[TAction]

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
            unexpanded_actions=self._legal_actions(rs),
            visits=0,
            value=0,
            action=None,
        )

        for _ in range(self._max_iterations):
            leaf = self._select(root)
            child = self._expand(leaf)
            value = self._simulate(child)

            # Back propagate each node
            node: _MctsTreeNode[TAction] | None = child
            while node is not None:
                node.visits += 1
                node.value += value
                node = node.parent

        if not root.children:
            return None, 0

        best = max(root.children, key=lambda c: c.visits)
        return best.action, 0

    # ------------------------------------------------------------------
    # MCTS phases
    # ------------------------------------------------------------------

    def _select(
        self,
        node: _MctsTreeNode[TAction],
    ) -> _MctsTreeNode[TAction]:
        while (
            not self._is_terminal(node.state)
            and not node.unexpanded_actions
            and node.children
        ):
            node = self._best_uct_child(node)

        return node

    def _expand(
        self,
        node: _MctsTreeNode[TAction],
    ) -> _MctsTreeNode[TAction]:
        if self._is_terminal(node.state):
            return node

        if not node.unexpanded_actions:
            return node

        action = node.unexpanded_actions.pop()

        child_state = self._apply_action(node.state, action)

        child = _MctsTreeNode(
            state=child_state,
            parent=node,
            children=[],
            action=action,
            unexpanded_actions=self._legal_actions(child_state),
            value=0,
            visits=0,
        )

        node.children.append(child)
        return child

    def _simulate(
        self,
        node: _MctsTreeNode[TAction],
    ) -> float:
        # TODO:
        # Run a rollout until terminal and return reward from
        # MAXIMIZING_FACTION's perspective.
        return node.state.get_score(MAXIMIZING_FACTION)

    # ------------------------------------------------------------------
    # Tree helpers
    # ------------------------------------------------------------------

    def _best_uct_child(
        self,
        node: _MctsTreeNode[TAction],
    ) -> _MctsTreeNode[TAction]:
        assert node.children

        log_parent = math.log(node.visits)

        def uct(child: _MctsTreeNode[TAction]) -> float:
            if child.visits == 0:
                return float("inf")

            exploitation = child.value / child.visits
            exploration = math.sqrt(2 * log_parent / child.visits)
            return exploitation + exploration

        return max(node.children, key=uct)

    # ------------------------------------------------------------------
    # Game-specific hooks (fill these in later)
    # ------------------------------------------------------------------

    def _legal_actions(
        self,
        state: IRepresentationState[TAction],
    ) -> list[TAction]:
        valid_actions: list[TAction] = []
        for action in state.get_actions():
            branch = state.get_one_branch(action)
            if branch == None:
                continue
            valid_actions.append(action)
        return valid_actions

    def _apply_action(
        self,
        state: IRepresentationState[TAction],
        action: TAction,
    ) -> IRepresentationState[TAction]:
        new_state = state.get_one_branch(action)
        assert new_state != None
        return new_state

    def _is_terminal(
        self,
        state: IRepresentationState[TAction],
    ) -> bool:
        return state.get_winner() != None
