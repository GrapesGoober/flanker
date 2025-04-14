"""
A simplified ECS architecture for game development. An Entity composes of components,
which are just dataclass for systems to run algorithms on. Component's lifecycle is
determined by its parent Entity.
"""


class Component:
    """
    Informal interface for lifecycle `on_add` and `on_remove` methods, called
    by `Scene` to reflect entity's lifcycle. Component instances must not be
    shared across entities.
    """

    def on_add(self) -> None: ...
    def on_remove(self) -> None: ...


class Entity:
    """
    An ECS Entity can hold logic, data, and components. Inherit this base class to create custom
    entity classes. Entities don't interact directly with each other, only through `Event`.
    """

    def __init__(self, *components: Component) -> None:
        self._components: list[Component] = list(components)

    @property
    def components(self) -> list[Component]:
        """A read-only components list. Once initialized, entity can't change this list."""
        return self._components


class Entities:
    """An Entity pool managing entities, their componenents, & lifecycle"""

    _entities: set[Entity] = set([])

    @staticmethod
    def add(*entities: Entity) -> None:
        """Adds a new entity to the game. Has no effect if entity is already added."""
        for entity in entities:
            if entity not in Entities._entities:
                Entities._entities.add(entity)
                for component in entity.components:
                    component.on_add()

    @staticmethod
    def remove(*entities: Entity) -> None:
        """Adds a new entity to the game. Has no effect if entity is not present."""
        for entity in entities:
            if entity in Entities._entities:
                Entities._entities.remove(entity)
                for component in entity.components:
                    component.on_remove()
