from dataclasses import dataclass
from typing import Any, Callable
from entity import Component


@dataclass
class Listener(Component):
    """An Event Listener component that calls the `callback` when event of type `topic` occurs."""

    topic: type
    callback: Callable[[Any], Any]

    def on_add(self) -> None:
        if self.topic in EventSystem.listeners:
            EventSystem.listeners[self.topic].append(self)
        else:
            EventSystem.listeners[self.topic] = [self]

    def on_remove(self) -> None:
        if self.topic in EventSystem.listeners:
            EventSystem.listeners[self.topic].remove(self)


class EventSystem:
    """System pool for listeners. Emitted events will automatically notify listeners."""

    listeners: dict[type, list[Listener]] = {}

    @staticmethod
    def emit(event: Any) -> list[Any]:
        """Emit a new event. Notifies any listener that subscribes to this topic."""
        responses: list[Any] = []
        if type(event) in EventSystem.listeners:
            for listener in EventSystem.listeners[type(event)]:
                response = listener.callback(event)
                if response is not None:
                    responses.append(response)
        return responses
