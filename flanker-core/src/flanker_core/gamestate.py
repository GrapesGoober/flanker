from copy import deepcopy
from typing import Any, Callable, overload
from uuid import UUID, uuid4


class GameState:
    """Encapsulates ECS entities & components into a game state."""

    def __init__(self) -> None:
        """Initializes the game state with empty entities."""
        self._entities: dict[UUID, dict[type[Any], Any]] = {}
        self._query_cache: dict[tuple[type, ...], list[UUID]] = {}
        self._systems: dict[type, type] = {}

    def register(self, cls: type[Any]) -> None:
        """Register a new system to game state."""
        if cls in self._systems:
            raise KeyError(f"System {cls} already exists.")
        self._systems[cls] = cls

    def replace(self, existing: type[Any], replacement: type[Any]) -> None:
        """Replace an existing registered system with a subclass variant."""
        if existing not in self._systems:
            raise KeyError(f"System {existing} does not exists")
        if not issubclass(replacement, existing):
            raise ValueError(
                f"Replacement {replacement} is not subclass of {existing}."
            )
        self._systems[existing] = replacement

    def get[T](self, cls: type[T]) -> type[T]:
        """Get a registered system."""
        if cls not in self._systems:
            raise KeyError(f"System {cls} does not exist.")
        return self._systems[cls]

    def add_entity(self, *components: Any, id: UUID | None = None) -> UUID:
        """Adds a new entity with the given components, returns ID."""
        if id in self._entities:
            raise ValueError(f"entity {id=} already exists")
        new_id = uuid4() if id is None else id
        self._entities[new_id] = {type(c): c for c in components}
        self._query_cache = {}
        return new_id

    def delete_entity(self, entity_id: UUID) -> None:
        """Deletes an entity by its ID"""
        self._entities.pop(entity_id)
        self._query_cache = {}

    def get_component[T](self, entity_id: UUID, component_type: type[T]) -> T:
        """Get an entity's component. None if entity or component not found."""
        if entity_id not in self._entities:
            raise KeyError(f"{entity_id=} doesn't exist.")
        if component_type not in self._entities[entity_id]:
            raise KeyError(f"{component_type=} missing for {entity_id=}.")
        return self._entities[entity_id][component_type]

    def try_component[T](self, entity_id: UUID, component_type: type[T]) -> T | None:
        return self._entities.get(entity_id, {}).get(component_type, None)

    @overload
    def query[T](
        self,
        t: type[T],
    ) -> list[tuple[UUID, T]]: ...

    @overload
    def query[T, U](
        self,
        t: type[T],
        u: type[U],
    ) -> list[tuple[UUID, T, U]]: ...

    @overload
    def query[T, U, V](
        self,
        t: type[T],
        u: type[U],
        v: type[V],
    ) -> list[tuple[UUID, T, U, V]]: ...

    def query(
        self,
        t: type,
        u: type | None = None,
        v: type | None = None,
    ) -> list[tuple[Any, ...]]:
        """Yields entities and their components by given component types."""
        component_types = tuple(filter(None, (t, u, v)))

        # If cache miss, linear search entities with matching component types
        if component_types not in self._query_cache:
            entity_ids: list[UUID] = [
                entity_id
                for entity_id, components in self._entities.items()
                if all(ct in components for ct in component_types)
            ]
            self._query_cache[component_types] = entity_ids

        # The entity IDs are matched; return their components
        result: list[tuple[Any, ...]] = []
        for entity_id in self._query_cache[component_types]:
            entity = self._entities[entity_id]
            components: list[Any] = [entity[ct] for ct in component_types]
            result.append((entity_id, *components))
        return result

    def dump(self) -> dict[UUID, dict[type, Any]]:
        """Returns a deep copy of the entities table."""
        return deepcopy(self._entities)

    @staticmethod
    def load(entities: dict[UUID, dict[type, Any]]) -> "GameState":
        """Loads game state from entities table and id counter."""
        gs = GameState()
        gs._entities = deepcopy(entities)
        return gs

    def selective_copy(
        self,
        *component_types: type[Any],
        copy_method: Callable[[Any], Any],
    ) -> "GameState":
        """Deep copies the selected components."""

        # Shallow copy everything by default
        new_gs = GameState()
        new_gs._entities = self._entities.copy()
        new_gs._query_cache = self._query_cache.copy()
        new_gs._systems = self._systems.copy()

        # Copies each entity dict and its component instances
        for entity_id in new_gs._entities:
            new_entity = new_gs._entities[entity_id].copy()
            new_gs._entities[entity_id] = new_entity

            # Copy its components based using specified method
            for component_type in new_entity:
                if component_type not in component_types:
                    continue
                new_component = copy_method(new_entity[component_type])
                new_entity[component_type] = new_component

        return new_gs
