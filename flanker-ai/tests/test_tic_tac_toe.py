import pytest
from flanker_ai.policies.minimax_policy import MinimaxPolicy
from flanker_ai.tic_tac_toe.actions import TicTacToeAction
from flanker_ai.tic_tac_toe.state import TicTacToeGameState
from flanker_core.models.components import InitiativeState


@pytest.fixture
def fixture() -> TicTacToeGameState:
    return TicTacToeGameState(
        board=[
            ["X", None, "O"],
            [None, "X", None],
            ["X", None, "O"],
        ],
        current_player=InitiativeState.Faction.BLUE,  # O
    )


def test_str_simple_board(fixture: TicTacToeGameState) -> None:

    expected = "\n".join(
        [
            "X . O",
            ". X .",
            "X . O",
        ]
    )

    assert str(fixture) == expected


def test_minimax_move(fixture: TicTacToeGameState) -> None:
    expected = "\n".join(
        [
            "X . O",
            ". X O",
            "X . O",
        ]
    )
    minimax = MinimaxPolicy[TicTacToeAction](depth=1)
    actions = minimax.get_action_sequence(fixture)
    action = actions[0]
    new_state = fixture.get_deterministic_branch(action)
    assert action == TicTacToeAction(row=1, column=2)
    assert str(new_state) == expected
