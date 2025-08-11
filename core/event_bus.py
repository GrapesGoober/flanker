from typing import Any, Callable
from core.gamestate import GameState

_HANDLERS: dict[Callable[[GameState, Any], None], type] = {}


class EventBus:

    @staticmethod
    def on[T](
        event_type: type[T],
    ) -> Callable[[Callable[[GameState, T], None]], Callable[[GameState, T], None]]:
        """Declares a function as an event handler."""

        def decorator(
            handler: Callable[[GameState, T], None],
        ) -> Callable[[GameState, T], None]:
            _HANDLERS[handler] = event_type
            return handler

        return decorator

    @staticmethod
    def get_handlers(
        *systems: type,
    ) -> list[tuple[Callable[[GameState, Any], None], type]]:
        """Discovered declared event handlers of static system classes"""
        return [
            (func, _HANDLERS[func])
            for system in systems
            for func in system.__dict__.values()
            if func in _HANDLERS
        ]
