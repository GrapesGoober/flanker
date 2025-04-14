"""
A simplified ECS architecture for game development. An Entity composes of components,
which are just dataclass for systems to run algorithms on. Component's lifecycle is
determined by its parent Entity.
"""

import random
from typing import Any, Type


class Component:
    """
    Informal interface for lifecycle `on_add` and `on_remove` methods, called
    by `GameState` to reflect entity's lifcycle. Component instances must not be
    shared across entities.
    """

    def on_add(self, gs: "GameState") -> None: ...
    def on_remove(self, gs: "GameState") -> None: ...


class Entity:
    """
    An ECS Entity can hold logic, data, and components. Inherit this base class to create custom
    entity classes. Entities don't interact directly with each other, only through events.
    """

    def __init__(self, gs: "GameState", *components: Component) -> None:
        self.gs = gs
        self._components: list[Component] = list(components)

    def __hash__(self) -> int:
        return int.from_bytes(random.randbytes(8))

    @property
    def components(self) -> list[Component]:
        """A read-only components list. Once initialized, entity can't change this list."""
        return self._components


class GameState:
    """Represents a self-contained game state. Contains entities, their components, & systems."""

    def __init__(self, *systems: Any) -> None:
        self._entities: set[Entity] = set([])
        self.system_pools: dict[type, Any] = {}
        for sys in systems:
            self.register(sys)

    def add(self, *entities: Entity) -> None:
        """Adds a new entity to the game."""
        for entity in entities:
            if entity in self._entities:
                raise Exception(f"Entity {entity} is already added.")
            self._entities.add(entity)
            for component in entity.components:
                component.on_add(self)

    def remove(self, *entities: Entity) -> None:
        """Removes an entity from the game."""
        for entity in entities:
            if entity not in self._entities:
                raise Exception(f"Entity {entity} doesn't exist.")
            self._entities.remove(entity)
            for component in entity.components:
                component.on_remove(self)

    def register(self, sys: Any) -> None:
        """Registers a new system. System can be any object."""
        if sys in self.system_pools:
            raise Exception(f"System {type(sys)} is already registered.")
        self.system_pools[type(sys)] = sys

    def system[T](self, cls: Type[T]) -> T:
        """Retrieves a registered system using its class type."""
        if cls not in self.system_pools:
            raise Exception(f"Can't get {cls}; system is not registered.")
        return self.system_pools[cls]
