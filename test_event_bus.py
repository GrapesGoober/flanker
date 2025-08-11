from dataclasses import dataclass
from core.event_bus import EventBus

@dataclass
class MoveEvent:...

class MockOnMove:

    @EventBus.on(MoveEvent)
    @staticmethod
    def on_move(event: MoveEvent) -> None:
        """Docstring"""
        print("moved")

MockOnMove.on_move(MoveEvent())