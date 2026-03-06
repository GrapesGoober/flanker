import pytest
from flanker_ai.policies.minimax_policy import MinimaxPolicy
from flanker_ai.states.tic_tac_toe_actions import TicTacToeAction
from flanker_ai.states.tic_tac_toe_state import TicTacToeState
from flanker_core.models.components import InitiativeState


@pytest.fixture
def tic_tac_toe_fixture() -> TicTacToeState:
    return TicTacToeState(
        board=[
            ["X", None, "O"],
            [None, "X", None],
            ["X", None, "O"],
        ],
        current_player=InitiativeState.Faction.BLUE,  # O
    )


def test_str_simple_board(tic_tac_toe_fixture: TicTacToeState) -> None:

    expected = "\n".join(
        [
            "X . O",
            ". X .",
            "X . O",
        ]
    )

    assert str(tic_tac_toe_fixture) == expected


def test_minimax_move(tic_tac_toe_fixture: TicTacToeState) -> None:
    expected = "\n".join(
        [
            "X . O",
            ". X O",
            "X . O",
        ]
    )
    minimax = MinimaxPolicy[TicTacToeAction](depth=1)
    actions = minimax.get_action_sequence(tic_tac_toe_fixture)
    action = actions[0]
    new_state = tic_tac_toe_fixture.get_deterministic_branch(action)
    assert action == TicTacToeAction(row=1, column=2)
    assert str(new_state) == expected
