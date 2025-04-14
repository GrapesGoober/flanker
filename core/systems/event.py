from typing import Type, Any, Callable
from dataclasses import dataclass
from systems.ecs import Component, GameState


@dataclass
class Listener(Component):
    """An Event Listener component that calls the `callback` when event of type `topic` occurs."""

    topic: type
    callback: Callable[[Any], Any]

    def on_add(self, gs: GameState) -> None:
        event_sys = gs.system(EventSystem)
        if self.topic in event_sys.listeners:
            event_sys.listeners[self.topic].append(self)
        else:
            event_sys.listeners[self.topic] = [self]

    def on_remove(self, gs: GameState) -> None:
        event_sys = gs.system(EventSystem)
        if self.topic in event_sys.listeners:
            event_sys.listeners[self.topic].remove(self)


class EventSystem:
    """System pool for listeners. Emitted events will automatically notify listeners."""

    def __init__(self) -> None:
        self.listeners: dict[type, list[Listener]] = {}

    def emit[T](self, event: Any, response_type: Type[T] = type(None)) -> list[T]:
        """
        Emit a new event. Notifies any listener that subscribes to this topic.
        If `response_type` is provided, return a list of type-guarded responses.
        If
        """
        responses: list[T] = []
        if type(event) in self.listeners:
            for listener in self.listeners[type(event)]:
                response = listener.callback(event)
                if isinstance(response, response_type) and response != None:
                    responses.append(response)
        return responses
