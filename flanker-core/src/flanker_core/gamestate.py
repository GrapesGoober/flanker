from copy import deepcopy
from typing import Any, overload


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
    def query[T](self, t: type[T]) -> list[tuple[int, T]]: ...

    @overload
    def query[T, U](self, t: type[T], u: type[U]) -> list[tuple[int, T, U]]: ...

    @overload
    def query[T, U, V](
        self, t: type[T], u: type[U], v: type[V]
    ) -> list[tuple[int, T, U, V]]: ...

    def query(
        self, t: type, u: type | None = None, v: type | None = None
    ) -> list[tuple[Any, ...]]:
        """Yields all entities with a specific component type."""
        component_types = tuple(filter(None, (t, u, v)))
        if component_types in self._cache:
            return self._cache[component_types]
        else:
            result: list[tuple[Any, ...]] = []
            for entity_id, components in self._entities.items():
                if all(ct in components for ct in component_types):
                    result.append(
                        (entity_id, *(components[ct] for ct in component_types))
                    )
            self._cache[component_types] = result
            return result

    def dump(self) -> tuple[dict[int, dict[type, Any]], int]:
        """Dump a copy of the entities table and id counter"""
        return deepcopy(self._entities), self._id_counter

    @staticmethod
    def load(
        entities: dict[int, dict[type, Any]],
        id_counter: int,
    ) -> "GameState":
        """Loads game state from entities table and id counter."""
        gs = GameState()
        gs._entities = deepcopy(entities)
        gs._id_counter = id_counter
        return gs

    def selective_copy(self, entity_ids: list[int]) -> "GameState":
        """Deep copies the selected entities, the rest shallow copy."""
        new_gs = GameState()
        # Shallow copy everything by default
        new_gs._entities = dict(self._entities)
        new_gs._id_counter = self._id_counter
        new_gs._cache = dict(self._cache)
        # Deep copy the selected entities.
        for id in entity_ids:
            if id not in new_gs._entities:
                raise KeyError(f"entity {id=} does not exist.")
            new_gs._entities[id] = deepcopy(self._entities[id])
            # Clear cache for selected entities.
            components = list(new_gs._entities[id].keys())
            for component_type in components:
                for cache_key in list(new_gs._cache.keys()):
                    if component_type in cache_key:
                        new_gs._cache.pop(cache_key)

        return new_gs
