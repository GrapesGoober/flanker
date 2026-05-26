import json
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, create_model


class Serializer:
    """Static class for game state's entity-components serialization."""

    class EntitiesTable[TEntity](BaseModel):
        """Defines the entities table data structure."""

        entities: dict[UUID, TEntity]

    @staticmethod
    def _get_entities_types(
        component_types: list[type],
    ) -> tuple[type[BaseModel], type[EntitiesTable[BaseModel]]]:
        """Build BaseModels of Entity and EntitiesTable using component types."""

        component_fields: dict[str, Any] = {
            t.__name__: (Optional[t], None) for t in component_types
        }
        # TODO: this create_model is security risk by executing arbitrary code
        # see https://docs.pydantic.dev/latest/examples/dynamic_models/
        Entity = create_model("Entity", **component_fields)
        EntitiesTable = create_model(
            "EntitiesTable", __base__=Serializer.EntitiesTable[Entity]
        )
        return Entity, EntitiesTable

    @staticmethod
    def get_entities_json_schema(
        component_types: list[type],
    ) -> str:
        _, EntitiesTable = Serializer._get_entities_types(component_types)
        schema = EntitiesTable.model_json_schema()
        return json.dumps(schema, indent=2)

    @staticmethod
    def serialize(
        entities: dict[UUID, dict[type, Any]],
        component_types: list[type],
    ) -> str:
        """Serialises entity-component table & id counter to json string"""

        # Create pydantic models using component types
        Entity, EntitiesTable = Serializer._get_entities_types(component_types)

        # Convert entities to pydantic models
        file_data = EntitiesTable(
            entities={
                # Each entity is validated using the built BaseModel
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
        Entity, EntitiesTable = Serializer._get_entities_types(component_types)
        file_data = EntitiesTable.model_validate_json(json_data)

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
