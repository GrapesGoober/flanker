from typing import Literal

import pytest
from flanker_ai.policies.mcts_policy import MctsPolicy
from flanker_ai.policies.minimax_policy import MinimaxPolicy
from flanker_ai.states.tic_tac_toe.tic_tac_toe_actions import TicTacToeAction
from flanker_ai.states.tic_tac_toe.tic_tac_toe_state import TicTacToeState
from flanker_core.models.components import InitiativeState


@pytest.fixture
def fixture() -> TicTacToeState:
    return TicTacToeState(
        board=[
            ["X", None, "O"],
            [None, "X", None],
            ["X", None, "O"],
        ],
        current_player=InitiativeState.Faction.BLUE,  # O
    )


def test_str_simple_board(fixture: TicTacToeState) -> None:

    expected = "\n".join(
        [
            "X . O",
            ". X .",
            "X . O",
        ]
    )

    assert str(fixture) == expected


@pytest.mark.parametrize("policy_type", ["Minimax", "MCTS"])
def test_minimax_move(
    fixture: TicTacToeState,
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
            policy = MinimaxPolicy[TicTacToeAction](depth=1)
        case "MCTS":
            policy = MctsPolicy[TicTacToeAction](max_iterations=10_000)

    action, _ = policy.get_action(fixture)
    assert action != None
    _, new_state = fixture.get_branches(action)[0]
    assert action == TicTacToeAction(row=1, column=2)
    assert str(new_state) == expected
