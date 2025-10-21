from uuid import UUID
from pydantic import BaseModel, create_model
from typing import Any, Optional, cast


class Serializer:
    """Static class for game state's entity-components serialization."""

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
        FileData = create_model("FileData", entities=dict[UUID, EntityComponent])
        # The dynamically built FileData type must conform to _FileDataType
        return EntityComponent, cast(type[Serializer.FileDataType], FileData)

    @staticmethod
    def serialize(
        entities: dict[UUID, list[Any]],
        component_types: list[type],
    ) -> str:
        """Serialises entity-component table to json string"""

        # Define file schema models using existing components
        EntityComponent, FileData = Serializer._build_schema(component_types)

        # Convert entities to using EntityComponent models
        file_data = FileData(
            entities={
                entity_id: EntityComponent(
                    **{
                        comp.__class__.__name__: comp
                        for comp in comps
                        if type(comp) in component_types
                    }
                )
                for entity_id, comps in entities.items()
            },
        )

        # Serialize with nulls excluded
        return file_data.model_dump_json(indent=2, exclude_none=True)

    @staticmethod
    def deserialize(
        json_data: str, component_types: list[type]
    ) -> dict[UUID, list[Any]]:
        """Deerialises entity-component table from json string"""

        # Serialize with nulls excluded
        EntityComponent, FileData = Serializer._build_schema(component_types)
        file_data = FileData.model_validate_json(json_data)

        # Convert EntityComponent models to dict[UUID, list[Any]] components
        entities: dict[UUID, list[Any]] = {
            entity_id: [
                comp_obj
                for comp_name in EntityComponent.model_fields.keys()
                if (comp_obj := getattr(entity_components, comp_name)) is not None
            ]
            for entity_id, entity_components in file_data.entities.items()
        }
        return entities
