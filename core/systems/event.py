from dataclasses import dataclass
from typing import Any, Callable

from systems.entity import Component

@dataclass
class Listener(Component):
    """ An Event Listener component that calls the `callback` when event of type `topic` occurs."""

    topic: type
    callback: Callable[[Any], Any]

    def on_add(self) -> None:
        if self.topic in Events.listeners:
            Events.listeners[self.topic].append(self)
        else:
            Events.listeners[self.topic] = [self]

    def on_remove(self) -> None:
        if self.topic in Events.listeners:
            Events.listeners[self.topic].remove(self)


class Events:
    """ System pool for listeners. Emitted events will automatically notify listeners. """
    listeners: dict[type, list[Listener]] = {}
    
    @staticmethod
    def emit(event: Any) -> list[Any]:
        """ Emit a new event. Notifies any listener that subscribes to this topic. """
        responses: list[Any] = []
        if type(event) in Events.listeners:
            for listener in Events.listeners[type(event)]:
                response = listener.callback(event)
                if response is not None: 
                    responses.append(response)
        return responses
