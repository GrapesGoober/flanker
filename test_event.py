from dataclasses import dataclass
from core.gamestate import GameState


@dataclass
class MoveEvent: ...


class MockMove:

    @GameState.on_event(MoveEvent)
    @staticmethod
    def on_move(gs: GameState, event: MoveEvent) -> None:
        """Docstring"""
        print("moved")


class MockFire:

    @GameState.on_event(MoveEvent)
    @staticmethod
    def check_interrupt(gs: GameState, event: MoveEvent) -> None:
        """Docstring"""
        print("check interrupt")


gs = GameState()
gs.register(MockMove, MockFire)
gs.emit(MoveEvent())
