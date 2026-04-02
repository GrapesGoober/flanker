from typing import Any, override


class ContextProvider:
    def __init__(self) -> None:
        self._systems: dict[type, Any] = {}

    def register(self, cls: type[Any]) -> None:
        self._systems[cls] = cls

    def replace(self, existing: type[Any], cls: type[Any]) -> None:
        if existing not in self._systems:
            raise ValueError(f"System {existing} not exists")
        if not issubclass(cls, existing):
            raise ValueError(f"Replacement {cls} is not subclass of {existing}")
        self._systems[existing] = cls

    def get[T](self, cls: type[T]) -> type[T]:
        return self._systems[cls]


class FooSystem:
    @staticmethod
    def do_thing() -> str:
        return "Foo is doing thing"


class BarSystem(FooSystem):
    @staticmethod
    @override
    def do_thing() -> str:
        return "Bar is doing thing"


ctx = ContextProvider()
ctx.register(FooSystem)
ctx.replace(existing=FooSystem, cls=BarSystem)

foo_system = ctx.get(FooSystem)
print(foo_system.do_thing())
