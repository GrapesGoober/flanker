from abc import ABC, abstractmethod
from typing import override

from flanker_core.serializer import Any


class ContextProvider:
    def __init__(self) -> None:
        self._systems: dict[type, Any] = {}

    def register[T](self, interface: type[T], cls: T) -> None:
        self._systems[interface] = cls

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
