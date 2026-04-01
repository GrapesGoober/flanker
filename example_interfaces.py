from abc import ABC, abstractmethod
from typing import override

from flanker_core.serializer import Any


class ContextProvider:
    def __init__(self) -> None:
        # Systems are objects, which is statically enforced (somewhat)
        # But this isn't ideal for how I treat systems.
        self._systems: dict[type, Any] = {}

    # This accepts an instance of system, but i want it static
    def register[T](self, base_cls: type[T], obj: T) -> None:
        self._systems[base_cls] = obj

    # This returns an instance of system. It's not color coded
    def get_system[T](self, interface: type[T]) -> T:
        return self._systems[interface]


class DoableSystem(ABC):
    @staticmethod
    @abstractmethod
    def do_thing() -> str: ...


class FooSystem(DoableSystem):
    @staticmethod
    @override
    def do_thina() -> str:
        return "This isn't overriding"


class BarSystem(DoableSystem):
    @staticmethod
    @override
    def do_thing() -> str:
        return "BarSystem is doing something"


def get_some() -> DoableSystem:
    return BarSystem()


ctx = ContextProvider()
ctx.register(DoableSystem, FooSystem())

doable = ctx.get_system(DoableSystem)
print(doable.do_thing())
