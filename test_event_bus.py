from dataclasses import dataclass
from core.event_bus import EventBus
from core.gamestate import GameState


@dataclass
class MoveEvent: ...


class MockMove:

    @EventBus.on(MoveEvent)
    @staticmethod
    def on_move(gs: GameState, event: MoveEvent) -> None:
        """Docstring"""
        print("moved")


class MockFire:

    @EventBus.on(MoveEvent)
    @staticmethod
    def check_interrupt(gs: GameState, event: MoveEvent) -> None:
        """Docstring"""
        print("check interrupt")


gs = GameState()
EventBus.register(gs, MockMove, MockFire)
gs.emit(MoveEvent())
