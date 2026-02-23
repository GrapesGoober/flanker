from copy import deepcopy
from dataclasses import dataclass
from typing import Literal, Optional, Sequence

from flanker_ai.i_game_state import IGameState
from flanker_core.models.components import InitiativeState

MARK = Literal["O"] | Literal["X"]

MARK_TO_FACTION: dict[MARK, InitiativeState.Faction] = {
    "O": InitiativeState.Faction.BLUE,
    "X": InitiativeState.Faction.RED,
}

FACTION_TO_MARK: dict[InitiativeState.Faction, MARK] = {
    InitiativeState.Faction.BLUE: "O",
    InitiativeState.Faction.RED: "X",
}


@dataclass
class TicTacToeAction:
    row: int
    column: int


class TicTacToeGameState(IGameState[TicTacToeAction]):

    def __init__(
        self,
        current_player: InitiativeState.Faction,
        board: list[list[MARK | None]] | None = None,
    ) -> None:
        if board is None:
            board = [[None for _ in range(3)] for _ in range(3)]
        self.board: list[list[MARK | None]] = board
        self.current_player: MARK = FACTION_TO_MARK[current_player]

    # ---------- Core Protocol Methods ----------

    def copy(self) -> "TicTacToeGameState":
        return TicTacToeGameState(
            current_player=MARK_TO_FACTION[self.current_player],
            board=deepcopy(self.board),
        )

    def get_winner(self) -> Optional[InitiativeState.Faction]:
        lines: list[list[MARK | None]] = []

        # Rows
        lines.extend(self.board)

        # Columns
        for col in range(3):
            lines.append([self.board[row][col] for row in range(3)])

        # Diagonals
        lines.append([self.board[i][i] for i in range(3)])
        lines.append([self.board[i][2 - i] for i in range(3)])

        for line in lines:
            if line[0] is not None and all(cell == line[0] for cell in line):
                return MARK_TO_FACTION[line[0]]

        return None

    def get_branches(
        self,
        action: TicTacToeAction,
    ) -> list["TicTacToeGameState"]:
        if self.get_winner() is not None:
            return []

        branches: list[TicTacToeGameState] = []
        if self.board[action.row][action.column] is None:
            new_state = self.copy()
            new_state.board[action.row][action.column] = self.current_player
            new_state.current_player = "X" if self.current_player == "O" else "O"
            branches.append(new_state)

        return branches

    def get_actions(self) -> Sequence[TicTacToeAction]:
        actions: list[TicTacToeAction] = []
        for r in range(3):
            for c in range(3):
                if self.board[r][c] is None:
                    actions.append(
                        TicTacToeAction(
                            row=r,
                            column=c,
                        )
                    )
        return actions

    def get_score(self) -> float:
        winner = self.get_winner()

        if winner == InitiativeState.Faction.BLUE:
            return 1.0
        elif winner == InitiativeState.Faction.RED:
            return -1.0

        # Draw
        if all(cell is not None for row in self.board for cell in row):
            return 0.0

        # Non-terminal heuristic (simple)
        return 0.0

    # ---------- Utility ----------

    def is_full(self) -> bool:
        return all(cell is not None for row in self.board for cell in row)

    def __str__(self) -> str:
        return "\n".join(
            " ".join(cell if cell is not None else "." for cell in row)
            for row in self.board
        )
