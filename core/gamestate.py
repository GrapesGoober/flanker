from typing import Any, Iterable


class GameState:
    """Encapsulates ECS entities & components into a game state."""

    def __init__(self) -> None:
        """Initializes the game state with empty entities."""
        self._id_counter: int = 0
        self._entities: dict[int, dict[type[Any], Any]] = {}
        self._cache: dict[type, list[tuple[int, Any]]] = {}

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

    def get_component[T](self, entity_id: int, component_type: type[T]) -> T | None:
        """Get an entity's component. None if entity or component not found."""
        return self._entities.get(entity_id, {}).get(component_type)

    def get_entities[T](self, component_type: type[T]) -> Iterable[tuple[int, T]]:
        """Yields all entities with a specific component type."""
        if component_type in self._cache:
            yield from self._cache[component_type]
        else:
            self._cache[component_type] = []
            for eid, comps in self._entities.items():
                comp = comps.get(component_type)
                if comp is not None:
                    self._cache[component_type].append((eid, comp))
                    yield (eid, comp)
