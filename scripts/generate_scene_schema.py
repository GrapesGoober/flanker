from dataclasses import is_dataclass
from inspect import isclass
from typing import Any

from flanker_ai.components import AiConfigComponent
from flanker_core.models import components
from flanker_core.serializer import Serializer


def get_component_types() -> list[type[Any]]:

    # How can I reference TerrainTypeTag?
    component_types: list[type[Any]] = []
    component_types.append(AiConfigComponent)
    for _, cls in vars(components).items():
        if isclass(cls) and is_dataclass(cls):
            component_types.append(cls)
    return component_types


if __name__ == "__main__":
    component_types = get_component_types()
    schema = Serializer.get_entities_json_schema(component_types)
    with open("./scripts/scene-schema.json", "w") as f:
        f.write(schema)
