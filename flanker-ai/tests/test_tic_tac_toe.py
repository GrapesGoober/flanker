import pytest
from flanker_ai.minimax_search import MinimaxSearch
from flanker_ai.tic_tac_toe_game_state import TicTacToeGameState
from flanker_core.models.components import InitiativeState


@pytest.fixture
def fixture() -> TicTacToeGameState:
    return TicTacToeGameState(
        board=[
            ["X", None, "O"],
            [None, "X", None],
            [None, None, "O"],
        ],
        current_player=InitiativeState.Faction.BLUE,  # O
    )


def test_str_simple_board(fixture: TicTacToeGameState) -> None:

    expected = "\n".join(
        [
            "X . O",
            ". X .",
            ". . O",
        ]
    )

    assert str(fixture) == expected


def test_minimax_move(fixture: TicTacToeGameState) -> None:
    expected = "\n".join(
        [
            "X . O",
            ". X O",
            ". . O",
        ]
    )
    _, new_state = MinimaxSearch.search(fixture, 1, True)
    print(new_state)
    assert str(new_state) == expected
