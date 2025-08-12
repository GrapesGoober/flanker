from typing import Any, Callable, Iterable
from core.gamestate import GameState

_HANDLERS: dict[Callable[[GameState, Any], None], type] = {}


class EventBus:

    @staticmethod
    def on[T](
        event_type: type[T],
    ) -> Callable[[Callable[[GameState, T], None]], Callable[[GameState, T], None]]:
        """Declares a callable as an event handler."""

        def decorator(
            handler: Callable[[GameState, T], None],
        ) -> Callable[[GameState, T], None]:
            _HANDLERS[handler] = event_type
            return handler

        return decorator

    @staticmethod
    def get_handlers(
        system: type,
    ) -> Iterable[tuple[Callable[[GameState, Any], None], type]]:
        """Discover declared event handlers of static system classes"""
        for func in system.__dict__.values():
            if func in _HANDLERS:
                yield (func, _HANDLERS[func])

    @staticmethod
    def register(gs: GameState, *systems: type) -> None:
        """Registers declared handlers as ECS systems to the game state."""
        for system in systems:
            for handler, event_type in EventBus.get_handlers(system):
                gs.add_handler(event_type, handler)
