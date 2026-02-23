from dataclasses import dataclass


@dataclass
class TicTacToeAction:
    row: int
    column: int
