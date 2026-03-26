from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, create_model


class Serializer:
    """Static class for game state's entity-components serialization."""

    class JsonSchema[TEntity](BaseModel):
        """Defines the output JSON data structure for serialization"""

        entities: dict[UUID, TEntity]

    @staticmethod
    def _build_json_schema(
        component_types: list[type],
    ) -> tuple[type[BaseModel], type[JsonSchema[BaseModel]]]:
        """Build Entity and JSON schema using component types."""

        component_fields: dict[str, Any] = {
            t.__name__: (Optional[t], None) for t in component_types
        }
        # TODO: this create_model is security risk by executing arbitrary code
        # see https://docs.pydantic.dev/latest/examples/dynamic_models/
        Entity = create_model("EntityComponent", **component_fields)
        JsonSchemaType = create_model(
            "FileData", __base__=Serializer.JsonSchema[Entity]
        )
        # The dynamically built FileData type must conform to _FileDataType
        return Entity, JsonSchemaType

    @staticmethod
    def serialize(
        entities: dict[UUID, dict[type, Any]],
        component_types: list[type],
    ) -> str:
        """Serialises entity-component table & id counter to json string"""

        # Define file schema models using existing components
        Entity, JsonSchema = Serializer._build_json_schema(component_types)

        # Convert entities to using EntityComponent models
        file_data = JsonSchema(
            entities={
                # Each entity is validated using built schema
                entity_id: Entity(
                    **{
                        comp.__class__.__name__: comp
                        for comp in comps.values()
                        # Filter out unregistered components
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
    ) -> dict[UUID, dict[type, Any]]:
        """Deerialises entity-component table & id counter from json string"""

        # Serialize with nulls excluded
        Entity, FileData = Serializer._build_json_schema(component_types)
        file_data = FileData.model_validate_json(json_data)

        # Convert EntityComponent models to dict[type, Any] components
        entities: dict[UUID, dict[type, Any]] = {
            entity_id: {
                type(comp_obj): comp_obj
                for comp_name in Entity.model_fields.keys()
                if (comp_obj := getattr(entity_components, comp_name)) is not None
            }
            for entity_id, entity_components in file_data.entities.items()
        }
        return entities
