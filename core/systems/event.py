from typing import Type
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
    def emit[T](event: Any, response_type: Type[T] = type(None)) -> list[T]:
        """
        Emit a new event. Notifies any listener that subscribes to this topic.
        If `response_type` is provided, return a list of type-guarded responses.
        If
        """
        responses: list[T] = []
        if type(event) in EventSystem.listeners:
            for listener in EventSystem.listeners[type(event)]:
                response = listener.callback(event)
                if isinstance(response, response_type) and response != None:
                    responses.append(response)
        return responses
