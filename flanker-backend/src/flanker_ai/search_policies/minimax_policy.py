from dataclasses import dataclass
from itertools import count
from math import inf

from flanker_ai.search_states.i_search_state import ISearchState
from flanker_core.models.components import InitiativeState

_MAXIMIZING_FACTION = InitiativeState.Faction.BLUE


@dataclass
class _TranspositionEntry:
    score: float
    depth_remaining: int


@dataclass
class MinimaxTreeNode[TAction]:
    state: ISearchState[TAction]
    children: list["MinimaxTreeEdge[TAction]"]


@dataclass
class MinimaxTreeEdge[TAction]:
    action: TAction
    node: MinimaxTreeNode[TAction]
    best_score: float


@dataclass
class MinimaxSearchLog[TAction]:
    tree_size: int
    tree_root: MinimaxTreeNode[TAction] | None = None


class MinimaxPolicy[TAction]:
    """
    Implements Minimax game-tree search with alpha-beta pruning.
    """

    @staticmethod
    def get_action(
        state: ISearchState[TAction],
        depth: int,
        log_with_tree: bool = False,
    ) -> tuple[TAction | None, MinimaxSearchLog[TAction]]:
        """
        Returns the best action and its search log given a current game state.
        """

        counter = count()

        root: MinimaxTreeNode[TAction] | None = None
        if log_with_tree:
            root = MinimaxTreeNode(state=state, children=[])

        _, action = MinimaxPolicy[TAction]._search(
            state=state,
            depth_remaining=depth,
            alpha=-inf,
            beta=inf,
            counter=counter,
            transposition_table={},
            log_tree_to_append=root,
        )
        return action, MinimaxSearchLog(
            tree_size=next(counter) - 1,
            tree_root=root,
        )

    @staticmethod
    def _search(
        state: ISearchState[TAction],
        depth_remaining: int,
        alpha: float,
        beta: float,
        counter: "count[int]",
        transposition_table: dict[object, _TranspositionEntry],
        log_tree_to_append: MinimaxTreeNode[TAction] | None,
    ) -> tuple[float, TAction | None]:

        next(counter)

        # Have early return for terminal states and leaf nodes.
        if state.get_winner() is not None or depth_remaining == 0:
            return state.get_score(_MAXIMIZING_FACTION), None
        actions = state.get_actions()
        if len(actions) == 0:  # No legal actions => lost
            return state.get_score(_MAXIMIZING_FACTION), None

        # Sort each (action, state) pair, so to expand good actions first.
        action_state: list[tuple[TAction, ISearchState[TAction]]] = []
        for action in actions:
            branch = state.get_one_branch(action)
            if branch == None:
                continue
            action_state.append((action, branch))
        action_state.sort(key=lambda pair: pair[1].get_score(_MAXIMIZING_FACTION))

        # Loop through each action and recursively expand tree
        is_maximizing = state.get_initiative() == _MAXIMIZING_FACTION
        best_score = -inf if is_maximizing else inf
        best_action: TAction | None = None
        for action, branch in action_state:
            child_node: MinimaxTreeNode[TAction] | None = None
            if log_tree_to_append:
                child_node = MinimaxTreeNode[TAction](
                    state=branch,
                    children=[],
                )

            new_branch_depth = depth_remaining - 1
            state_key = branch.get_hashable_key()
            cached_entry = transposition_table.get(state_key)

            # Reuse the cached score value if exist, but also only if the
            # cached entry is more near-root than the current ply.
            if (
                cached_entry is not None
                and cached_entry.depth_remaining >= new_branch_depth
            ):
                score = cached_entry.score
            else:
                score, _ = MinimaxPolicy[TAction]._search(
                    state=branch,
                    depth_remaining=new_branch_depth,
                    alpha=alpha,
                    beta=beta,
                    counter=counter,
                    transposition_table=transposition_table,
                    log_tree_to_append=child_node,
                )
                transposition_table[state_key] = _TranspositionEntry(
                    score=score,
                    depth_remaining=new_branch_depth,
                )

            # Have scores be closer to zero the further down the tree.
            # This numbs the impact of future gains or future losses.
            # Ex: future wins is less preferable than closer wins.
            score = score * 0.9

            if log_tree_to_append is not None and child_node is not None:
                log_tree_to_append.children.append(
                    MinimaxTreeEdge[TAction](
                        action=action,
                        node=child_node,
                        best_score=score,
                    )
                )

            # Update score and handle alpha-beta pruning
            if is_maximizing:
                if score > best_score:
                    best_score = score
                    best_action = action
                alpha = max(alpha, best_score)
            else:
                if score < best_score:
                    best_score = score
                    best_action = action
                beta = min(beta, best_score)
            if beta <= alpha:
                break  # Skip subtree if cutoff

        return best_score, best_action
