from dataclasses import is_dataclass
from inspect import isclass
from typing import Iterable, Optional, cast, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, create_model
from backend.tag_components import TerrainTypeTag
from core import components
from core.serializer import Serializer

def _get_component_types() -> Iterable[type[Any]]:
    for _, cls in vars(components).items():
        if isclass(cls) and is_dataclass(cls):
            yield cls
    yield TerrainTypeTag

scene_name = "demo-old"
component_types = list(_get_component_types())
with open(f"./scenes/{scene_name}.json", "r") as f:
    entities, _ = Serializer.deserialize(f.read(), component_types)

new_entities = {uuid4() : comps for comps in entities.values()}

class FileDataType(BaseModel):
    """Defines the output file data structure for serialization"""

    entities: dict[UUID, BaseModel]

@staticmethod
def _build_schema(
    component_types: list[type],
) -> tuple[type[BaseModel], type[FileDataType]]:
    """Build (EntityComponent, FileData) schemas using component types."""

    component_fields: dict[str, Any] = {
        t.__name__: (Optional[t], None) for t in component_types
    }
    EntityComponent = create_model("EntityComponent", **component_fields)
    FileData = create_model(
        "FileData", entities=dict[UUID, EntityComponent]
    )
    # The dynamically built FileData type must conform to _FileDataType
    return EntityComponent, cast(type[FileDataType], FileData)

@staticmethod
def serialize(
    entities: dict[int, dict[type, Any]],
    component_types: list[type],
) -> str:
    """Serialises entity-component table & id counter to json string"""

    # Define file schema models using existing components
    EntityComponent, FileData = _build_schema(
        [comp_type for comps in entities.values() for comp_type in comps]
    )

    # Convert entities to using EntityComponent models
    file_data = FileData(
        entities={
            entity_id: EntityComponent(
                **{
                    comp.__class__.__name__: comp
                    for comp in comps.values()
                    if type(comp) in component_types
                }
            )
            for entity_id, comps in entities.items()
        },
    )

    # Serialize with nulls excluded
    return file_data.model_dump_json(indent=2, exclude_none=True)

    
with open(f"./scenes/{scene_name}.json", "w") as f:
    f.write(serialize(new_entities, component_types))