import random
from typing import Any


class Component:
    def __init__(self) -> None: ...
    def on_add(self, gs: "GameState", ent: "Entity") -> None: ...
    def on_remove(self, gs: "GameState", ent: "Entity") -> None: ...


class Entity:
    def __init__(self, *components: Component) -> None:
        self.id = hash(random.random())
        self._components: dict[type[Component], Component] = {}
        for component in components:
            if type(component) in self._components:
                raise ValueError(f"Component of type {type(component)} already added")
            self._components[type(component)] = component

    @property
    def components(self) -> list[Component]:
        return list(self._components.values())

    def get(self, component_type: type[Component]) -> Component:
        if component_type not in self._components:
            raise ValueError(f"Component of type {component_type} not found")
        return self._components[component_type]

    def __hash__(self) -> int:
        return self.id


class GameState:
    def __init__(self) -> None:
        self._entities: set[Entity] = set()
        self._system_pools: dict[type, Any] = {}

    def add(self, *entities: Entity) -> None:
        for entity in entities:
            if entity in self._entities:
                raise Exception(f"Entity {entity} is already added.")
            self._entities.add(entity)
            for component in entity.components:
                component.on_add(self, entity)

    def remove(self, *entities: Entity) -> None:
        for entity in entities:
            if entity not in self._entities:
                raise Exception(f"Entity {entity} doesn't exist.")
            self._entities.remove(entity)
            for component in entity.components:
                component.on_remove(self, entity)

    def get(self, entity_id: int) -> Entity:
        for entity in self._entities:
            if entity.id == entity_id:
                return entity
        raise ValueError(f"Entity with ID {entity_id} not found")

    def register(self, sys: Any) -> None:
        if sys in self._system_pools:
            raise Exception(f"System {type(sys)} is already registered.")
        self._system_pools[type(sys)] = sys

    def system[T](self, cls: type[T]) -> T:
        if cls not in self._system_pools:
            raise Exception(f"Can't get {cls}; system is not registered.")
        return self._system_pools[cls]


class MoveInputHandler(Component): ...


class ComponentA(Component): ...


class ComponentB(Component): ...


class ComponentC(Component): ...


class MovementControls(Component):
    def __init__(self, c: Component) -> None:
        self.c = c

    def on_move(self) -> None: ...


myfoo = Entity(
    ComponentA(),
    ComponentB(),
    ComponentC(),
    l := MoveInputHandler(),
    MovementControls(l),
)
