import json
from typing import Any, Iterable, Iterator, overload

from pydantic import TypeAdapter


class GameState:
    """Encapsulates ECS entities & components into a game state."""

    def __init__(self) -> None:
        """Initializes the game state with empty entities."""
        self._id_counter: int = 0
        self._entities: dict[int, dict[type[Any], Any]] = {}
        self._cache: dict[tuple[type, ...], list[tuple[int, Any]]] = {}

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

    def save(self) -> str:
        serialized = {}
        for entity_id, components in self._entities.items():
            serialized[entity_id] = {}
            for comp_type, comp_instance in components.items():
                comp_adapter = TypeAdapter(comp_type)
                comp_key = comp_type.__name__
                serialized[entity_id][comp_key] = comp_adapter.dump_python(
                    comp_instance, mode="json"
                )

        return json.dumps(serialized, indent=2)

    @staticmethod
    def load(data: str, component_types: list[type]) -> "GameState":
        raw = json.loads(data)
        gs = GameState()

        adapters: dict[str, TypeAdapter[Any]] = {}
        for comp_type in component_types:
            adapters[comp_type.__name__] = TypeAdapter(comp_type)

        for entity_id_str, components_raw in raw.items():
            entity_id = int(entity_id_str)
            entity_components: dict[type[Any], Any] = {}
            for comp_name, comp_values in components_raw.items():
                if comp_name not in adapters:
                    raise ValueError(f"Component {comp_name} is not recognized")
                adapter = adapters[comp_name]
                comp_instance = adapter.validate_python(comp_values)
                entity_components[type(comp_instance)] = comp_instance

            gs._entities[entity_id] = entity_components
            if entity_id > gs._id_counter:
                gs._id_counter = entity_id

        return gs
