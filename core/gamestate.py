from typing import Any, Callable, Iterable, Iterator, overload
from core.serializer import Serializer

_REGISTRY: dict[Callable[["GameState", Any], None], type] = {}


class GameState:
    """Encapsulates ECS entities & components into a game state."""

    def __init__(self) -> None:
        """Initializes the game state with empty entities."""
        self._id_counter: int = 0
        self._entities: dict[int, dict[type[Any], Any]] = {}
        self._cache: dict[tuple[type, ...], list[tuple[int, Any]]] = {}
        self._event_handlers: dict[type, list[Callable[[GameState, Any], None]]] = {}

    def add_entity(self, *components: Any) -> int:
        """Adds a new entity with the given components, returns ID."""
        entity_id = self._id_counter
        self._id_counter += 1
        self._entities[entity_id] = {type(c): c for c in components}
        self._cache = {}
        return entity_id

    def delete_entity(self, entity_id: int) -> None:
        """Deletes an entity by its ID"""
        self._entities.pop(entity_id)
        self._cache = {}

    def get_component[T](self, entity_id: int, component_type: type[T]) -> T:
        """Get an entity's component. None if entity or component not found."""
        if entity_id not in self._entities:
            raise KeyError(f"{entity_id=} doesn't exist")
        if component_type not in self._entities[entity_id]:
            raise KeyError(f"{component_type=} missing for {entity_id=}")
        return self._entities[entity_id][component_type]

    def try_component[T](self, entity_id: int, component_type: type[T]) -> T | None:
        return self._entities.get(entity_id, {}).get(component_type, None)

    @overload
    def query[T](self, t: type[T]) -> Iterator[tuple[int, T]]: ...

    @overload
    def query[T, U](self, t: type[T], u: type[U]) -> Iterator[tuple[int, T, U]]: ...

    @overload
    def query[T, U, V](
        self, t: type[T], u: type[U], v: type[V]
    ) -> Iterator[tuple[int, T, U, V]]: ...

    def query(
        self, t: type, u: type | None = None, v: type | None = None
    ) -> Iterable[tuple[Any, ...]]:
        """Yields all entities with a specific component type."""
        component_types = tuple(filter(None, (t, u, v)))
        if component_types in self._cache:
            yield from self._cache[component_types]
        else:
            for entity_id, components in self._entities.items():
                if all(
                    ct in components for ct in component_types
                ):  # Check all component types exist
                    yield (entity_id, *(components[ct] for ct in component_types))

    @staticmethod
    def on_event[T](
        event_type: type[T],
    ) -> Callable[  # Returns the same method without modifying
        [Callable[["GameState", T], None]],
        Callable[["GameState", T], None],
    ]:
        """Decorator that declares a callable as an event handler."""

        def decorator(
            handler: Callable[[GameState, T], None],
        ) -> Callable[[GameState, T], None]:
            _REGISTRY[handler] = event_type
            return handler

        return decorator

    def register(self, *systems: type) -> None:
        """Registers declared handlers as ECS systems."""
        for system in systems:
            for func in system.__dict__.values():
                if func in _REGISTRY:
                    event_type = _REGISTRY[func]
                    self._event_handlers.setdefault(event_type, [])
                    self._event_handlers[event_type].append(func)

    def emit(self, event: object) -> None:
        if type(event) not in self._event_handlers:
            return
        for handlers in self._event_handlers[type(event)]:
            handlers(self, event)

    def save(self) -> str:
        """Saves game state to json string."""
        return Serializer.serialize(self._entities, self._id_counter)

    @staticmethod
    def load(data: str, component_types: list[type]) -> "GameState":
        """Loads game state from json string."""
        gs = GameState()
        gs._entities, gs._id_counter = Serializer.deserialize(data, component_types)
        return gs
