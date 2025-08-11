from typing import Any, Callable


class EventBus:

    _REGISTRY: dict[type, list[Callable[[Any], None]]] = {}

    @staticmethod
    def on[T](
        event_type: type[T],
    ) -> Callable[[Callable[[T], None]], Callable[[T], None]]:
        def decorator(func: Callable[[T], None]) -> Callable[[T], None]:
            print(f"registered {func} for {event_type}")
            EventBus._REGISTRY.setdefault(event_type, [])
            EventBus._REGISTRY[event_type].append(func)
            return func

        return decorator
