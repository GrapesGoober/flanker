from dataclasses import dataclass
from typing import Literal

import pytest
from flanker_ai.search_policies.mcts_policy import MctsPolicy
from flanker_ai.search_policies.minimax_policy import MinimaxPolicy
from flanker_ai.search_policies.random_policy import RandomPolicy
from flanker_ai.search_states.i_search_state import ISearchState
from flanker_ai.search_states.tic_tac_toe.tic_tac_toe_actions import TicTacToeAction
from flanker_ai.search_states.tic_tac_toe.tic_tac_toe_state import TicTacToeState
from flanker_core.models.components import InitiativeState


@dataclass
class Fixture:
    state: TicTacToeState


@pytest.fixture
def fixture() -> Fixture:
    return Fixture(
        state=TicTacToeState(
            board=[
                ["X", None, "O"],
                [None, "X", None],
                ["X", None, "O"],
            ],
            current_player=InitiativeState.Faction.BLUE,  # O
        )
    )


def test_str_simple_board(fixture: Fixture) -> None:

    expected = "\n".join(
        [
            "X . O",
            ". X .",
            "X . O",
        ]
    )

    assert str(fixture.state) == expected


@pytest.mark.parametrize("policy_type", ["Minimax", "MCTS"])
def test_optimal_action(
    fixture: Fixture,
    policy_type: Literal["Minimax", "MCTS"],
) -> None:
    expected = "\n".join(
        [
            "X . O",
            ". X O",
            "X . O",
        ]
    )
    match policy_type:
        case "Minimax":
            action, _ = MinimaxPolicy[TicTacToeAction].get_action(
                state=fixture.state,
                depth=1,
            )
        case "MCTS":

            def simulate_policy(
                rs: ISearchState[TicTacToeAction],
            ) -> TicTacToeAction | None:
                action, _ = RandomPolicy[TicTacToeAction]().get_action(rs)
                return action

            action, _ = MctsPolicy[TicTacToeAction].get_action(
                rs=fixture.state,
                max_iterations=10_000,
                max_simulate_length=20,
                simulate_policy=simulate_policy,
            )

    assert action != None
    _, new_state = fixture.state.get_branches(action)[0]
    assert action == TicTacToeAction(row=1, column=2)
    assert str(new_state) == expected


def test_mcts_takes_immediate_win_as_red() -> None:
    """
    The MCTS used to have a bug where the simulations results are
    not backpropagated correctly. This test is to catch that the
    early RED (X) wins should be caught.
    """

    state = TicTacToeState(
        board=[
            ["X", "X", None],  # The RED should place X here.
            ["O", "O", None],
            [None, None, None],
        ],
        current_player=InitiativeState.Faction.RED,
    )

    # Use a greedy simulation policy. The best action for RED is
    # already obvious, so this is to reflect that sentiment.
    def simulate_policy(
        rs: ISearchState[TicTacToeAction],
    ) -> TicTacToeAction | None:
        for action in rs.get_actions():
            branch = rs.get_one_branch(action)
            if branch is not None and branch.get_winner() == rs.get_initiative():
                return action
        actions = rs.get_actions()
        return actions[0] if actions else None

    action, _ = MctsPolicy[TicTacToeAction].get_action(
        rs=state,
        max_iterations=1_000,
        max_simulate_length=20,
        simulate_policy=simulate_policy,
    )

    assert action == TicTacToeAction(row=0, column=2)
