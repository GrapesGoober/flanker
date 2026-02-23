import pytest
from flanker_ai.tic_tac_toe_game_state import TicTacToeGameState
from flanker_core.models.components import InitiativeState


@pytest.fixture
def fixture() -> TicTacToeGameState:
    return TicTacToeGameState(
        board=[
            ["X", "O", None],
            [None, "X", None],
            [None, None, "O"],
        ],
        current_player=InitiativeState.Faction.BLUE,
    )


def test_str_simple_board(fixture: TicTacToeGameState) -> None:

    expected = "X O .\n" ". X .\n" ". . O"

    assert str(fixture) == expected
