from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

from flanker_ai.search_states.i_search_state import ISearchState
from flanker_core.models.components import InitiativeState


@dataclass
class MctsTreeNode[TAction]:
    state: ISearchState[TAction]
    parent: "MctsTreeNode[TAction] | None"

    children: list["MctsTreeNode[TAction]"]
    unexpanded_actions: list[TAction]

    total_visits: int  # N(v) total number of visits
    total_value: float  # Q(v) total subtree reward from root's perspective

    action: TAction | None


@dataclass
class MctsSearchLog[TAction]:
    tree_depth: int
    tree_root: MctsTreeNode[TAction]


class MctsPolicy[TAction]:

    @staticmethod
    def get_action(
        rs: ISearchState[TAction],
        max_iterations: int,
        max_simulate_length: int,
        simulate_policy: Callable[[ISearchState[TAction]], TAction | None],
    ) -> tuple[TAction | None, MctsSearchLog[TAction]]:
        root_faction = rs.get_initiative()
        root = MctsTreeNode(
            state=rs,
            parent=None,
            children=[],
            unexpanded_actions=list(rs.get_actions()),
            total_visits=0,
            total_value=0,
            action=None,
        )

        # Expand the game tree. MCTS is stop-any-time, so run
        # until _max_iterations to stop, as deep as it needs.
        max_depth = 0
        for _ in range(max_iterations):

            # Choose a leaf node with best UCT, and expand its leaves
            leaf = MctsPolicy[TAction]._select_leaf_best_uct(root, root_faction)
            child = MctsPolicy[TAction]._expand(leaf)
            value = MctsPolicy[TAction]._simulate(
                node=child,
                max_simulate_length=max_simulate_length,
                simulate_policy=simulate_policy,
                root_faction=root_faction,
            )

            # Back propagate each node (while tracking depth)
            depth = 0
            node: MctsTreeNode[TAction] | None = child
            while node is not None:
                node.total_visits += 1
                node.total_value += value
                node = node.parent
                depth += 1
            max_depth = max(max_depth, depth)

        # No valid actions at this root
        if not root.children:
            return None, MctsSearchLog(
                tree_depth=max_depth,
                tree_root=root,
            )

        # Choose the root's best action to perform
        best = max(root.children, key=lambda c: c.total_visits)
        return best.action, MctsSearchLog(
            tree_depth=max_depth,
            tree_root=root,
        )

    @staticmethod
    def _select_leaf_best_uct(
        node: MctsTreeNode[TAction],
        root_faction: InitiativeState.Faction,
    ) -> MctsTreeNode[TAction]:
        """Search node's subtree for leaf node with max UCT."""

        current_node: MctsTreeNode[TAction] = node
        # Keep traversing down the node's subtree and choose a non-terminal leaf
        while (
            current_node.state.get_winner() == None  # Non-terminal
            and current_node.unexpanded_actions == []  # No actions unexpanded
            and current_node.children != []  # Has children to select from
        ):
            log_parent = math.log(current_node.total_visits)
            maximizing = current_node.state.get_initiative() == root_faction

            def uct(child: MctsTreeNode[TAction]) -> float:
                if child.total_visits == 0:  # unvisited nodes chosen first
                    return float("inf")

                exploitation = child.total_value / child.total_visits
                if not maximizing:
                    exploitation = -exploitation
                exploration = math.sqrt(2 * log_parent / child.total_visits)
                return exploitation + exploration

            current_node = max(current_node.children, key=uct)

        return current_node

    @staticmethod
    def _expand(
        node: MctsTreeNode[TAction],
    ) -> MctsTreeNode[TAction]:
        """
        Find a legal unexpanded action and expand it into a new child.
        """

        # Ignore expansion if terminal or if no expandable actions left.
        if node.state.get_winner() != None:
            return node
        if node.unexpanded_actions == []:
            return node

        # Find the first legal action and its resulting state
        legal_action = node.unexpanded_actions.pop()
        child_state = node.state.get_one_branch(legal_action)
        if child_state is None:
            raise Exception("Action invalid!")

        child = MctsTreeNode(
            state=child_state,
            parent=node,
            children=[],
            action=legal_action,
            unexpanded_actions=list(child_state.get_actions()),
            total_value=0,
            total_visits=0,
        )
        node.children.append(child)
        return child

    @staticmethod
    def _simulate(
        node: MctsTreeNode[TAction],
        max_simulate_length: int,
        simulate_policy: Callable[[ISearchState[TAction]], TAction | None],
        root_faction: InitiativeState.Faction,
    ) -> float:

        # Make a copy so it doesn't mutate the node itself
        current_state = node.state.copy()

        # Run simulation until hit the max limit
        stagnate_counter: int = 0
        for _ in range(max_simulate_length):
            if current_state.get_winner() != None:
                break
            if stagnate_counter >= 2:
                break

            # Pick a legal action to perform
            action = simulate_policy(current_state)

            # If no legal action found, pass initiative
            if action == None:
                current_state.flip_initiative()
                stagnate_counter += 1
                continue

            stagnate_counter = 0
            current_state.perform_action(action)

        winner = current_state.get_winner()
        if winner is None:
            return 0
        return 1 if winner == root_faction else -1
