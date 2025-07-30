from dataclasses import dataclass, is_dataclass
from typing import Any

from pydantic import TypeAdapter

# Global list of registered component classes
COMP_ADAPTERS: dict[str, TypeAdapter[Any]] = {}
COMP_TYPES: dict[str, type[Any]] = {}
COMP_KEYS: dict[type, str] = {}


def component[T](cls: type[T]) -> type[T]:

    # Make the class a dataclass (if it isn’t already)
    if not is_dataclass(cls):
        cls = dataclass(cls)

    # Register the class
    key = cls.__name__
    COMP_ADAPTERS[key] = TypeAdapter(cls)
    COMP_TYPES[key] = cls
    COMP_KEYS[cls] = key

    return cls
