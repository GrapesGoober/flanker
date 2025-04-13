"""
Entity system for game development ECS architecture. An Entity composes of components, which are just dataclass 
for systems to run algorithms on. Component's lifecycle is determined by parent Entity. 
"""

class Component:
    """ A component is an informal interface for lifecycle `on_add` and `on_remove` methods. """
    def on_add(self): ...
    def on_remove(self): ...

class Entity:
    """ An Entity base class. Entity can hold logic, data, and components.
        This base class is meant to be inherited to create custom entity classes. """

    def __init__(self, *components: Component) -> None:
        self.components: list[Component] = list(components)

    def add_component(self, component: Component) -> None:
        """ Assigns a new component to this entity. The lifetime of this component is matched tot this entity. """
        if component not in self.components:
            self.components.append(component)
            if self in Entities.entities:
                component.on_add()
    
    def remove_component(self, component: Component) -> None:
        if component in self.components:
            self.components.remove(component)
            if self in Entities.entities:
                component.on_remove()

class Entities:
    """ An Entity system pool. Manages lifetimes for entities & their components. """
    entities: list['Entity'] = []

    @staticmethod
    def add(*entities: Entity) -> None:
        for g in entities:
            if g not in Entities.entities:
                Entities.entities.append(g)
                for c in g.components:
                    c.on_add()
                    
    @staticmethod
    def remove(*entities: Entity) -> None:
        for g in entities:
            if g in Entities.entities:
                Entities.entities.remove(g)
                for c in g.components:
                    c.on_remove()

