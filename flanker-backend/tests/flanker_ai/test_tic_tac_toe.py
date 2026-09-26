from typing import Literal

import pytest
from flanker_ai.search_policies.mcts_policy import MctsPolicy
from flanker_ai.search_policies.minimax_policy import MinimaxPolicy
from flanker_ai.search_policies.random_policy import RandomPolicy
from flanker_ai.search_states.i_search_state import ISearchState
from flanker_ai.search_states.tic_tac_toe.tic_tac_toe_actions import TicTacToeAction
from flanker_ai.search_states.tic_tac_toe.tic_tac_toe_state import TicTacToeState
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
def test_optimal_action(
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

            def simulate_policy(
                rs: ISearchState[TicTacToeAction],
            ) -> TicTacToeAction | None:
                action, _ = RandomPolicy[TicTacToeAction]().get_action(rs)
                return action

            policy = MctsPolicy[TicTacToeAction](
                max_iterations=10_000,
                max_simulate_length=20,
                simulate_policy=simulate_policy,
            )

    action, _ = policy.get_action(fixture)
    assert action != None
    _, new_state = fixture.get_branches(action)[0]
    assert action == TicTacToeAction(row=1, column=2)
    assert str(new_state) == expected
