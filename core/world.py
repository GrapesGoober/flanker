from typing import Any, Iterable


class World:
    def __init__(self) -> None:
        self._id_counter: int = 0
        self._entities: dict[int, dict[type[Any], Any]] = {}
        self._systems: dict[type, Any] = {}

    def add_entity(self, *components: Any) -> int:
        entity_id = self._id_counter
        self._id_counter += 1
        self._entities[entity_id] = {type(c): c for c in components}
        return entity_id

    def delete_entity(self, entity_id: int) -> None:
        self._entities.pop(entity_id)

    def get_component[T](self, entity_id: int, component_type: type[T]) -> T | None:
        return self._entities.get(entity_id, {}).get(component_type)

    def get_entities[T](self, component_type: type[T]) -> Iterable[tuple[int, T]]:
        for eid, comps in self._entities.items():
            comp = comps.get(component_type)
            if comp is not None:
                yield (eid, comp)
