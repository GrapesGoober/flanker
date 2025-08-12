from dataclasses import dataclass
from core.event_registry import EventRegistry
from core.gamestate import GameState


@dataclass
class MoveEvent: ...


class MockMove:

    @EventRegistry.on(MoveEvent)
    @staticmethod
    def on_move(gs: GameState, event: MoveEvent) -> None:
        """Docstring"""
        print("moved")


class MockFire:

    @EventRegistry.on(MoveEvent)
    @staticmethod
    def check_interrupt(gs: GameState, event: MoveEvent) -> None:
        """Docstring"""
        print("check interrupt")


gs = GameState()
registry = EventRegistry(gs, MockMove, MockFire)
gs.events = registry
gs.events.emit(MoveEvent())
