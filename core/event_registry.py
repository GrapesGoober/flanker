from collections.abc import Callable
from typing import Any
from core.gamestate import GameState, IEventRegistry

_DECLARED_EVENTS: dict[Callable[[GameState, Any], None], type] = {}


class EventRegistry(IEventRegistry):

    def __init__(self, gs: GameState, *systems: type) -> None:
        self.gs = gs
        self._event_handlers: dict[type, list[Callable[[GameState, Any], None]]] = {}

        for system in systems:
            for func in system.__dict__.values():
                if func in _DECLARED_EVENTS:
                    event_type = _DECLARED_EVENTS[func]
                    self._event_handlers.setdefault(event_type, [])
                    self._event_handlers[event_type].append(func)

    @staticmethod
    def on[T](
        event_type: type[T],
    ) -> Callable[  # Returns the same method without modifying
        [Callable[["GameState", T], None]],
        Callable[["GameState", T], None],
    ]:
        """Decorator that declares a callable as an event handler."""

        def decorator(
            handler: Callable[[GameState, T], None],
        ) -> Callable[[GameState, T], None]:
            _DECLARED_EVENTS[handler] = event_type
            return handler

        return decorator

    def emit(self, event: object) -> None:
        if type(event) not in self._event_handlers:
            return
        for handlers in self._event_handlers[type(event)]:
            handlers(self.gs, event)
