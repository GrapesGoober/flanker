import pytest
from flanker_ai.minimax_search import MinimaxSearch
from flanker_ai.tic_tac_toe_game_state import TicTacToeAction, TicTacToeGameState
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
    _, action = MinimaxSearch.search(fixture, 1, True)
    assert action != None, "One optimal solution exists!"
    new_state = fixture.get_branches(action)
    assert action == TicTacToeAction(row=1, column=2)
    assert str(new_state[0]) == expected
