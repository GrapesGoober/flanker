import inspect
import json
from typing import Any, Optional
from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
    SerializerFunctionWrapHandler,
    create_model,
    model_serializer,
)


class Serializer:
    """Static class for game state's entity-components serialization."""

    class _EntitiesTable[TEntity](BaseModel):
        """Defines the entities table serialized data structure."""

        entities: dict[UUID, TEntity]

    class _SparseEntity(BaseModel):
        """
        Defines custom serialization that ignores `None` fields.
        This is similiar to `exclude_none=True` but is not recursive.
        """

        @model_serializer(mode="wrap")
        def serialize_model(
            self, handler: SerializerFunctionWrapHandler
        ) -> dict[str, object]:
            data: dict[str, Any] = handler(self)
            return {key: val for key, val in data.items() if val is not None}

    @staticmethod
    def _get_entities_types(
        component_types: list[type],
    ) -> tuple[type[_SparseEntity], type[_EntitiesTable[_SparseEntity]]]:
        """Build BaseModels of Entity and EntitiesTable using component types."""

        # Build a table of component to its type, default value, and description
        component_fields: dict[str, Any] = {}
        for t in component_types:
            component_fields[t.__name__] = (
                Optional[t],
                Field(default=None, description=inspect.getdoc(t)),
            )

        # NOTE: create_model has security risk by executing arbitrary code.
        # Never use type annotations from untrusted input.
        Entity = create_model(
            "Entity",
            __base__=Serializer._SparseEntity,
            **component_fields,
        )
        EntitiesTable = create_model(
            "EntitiesTable",
            __base__=Serializer._EntitiesTable[Entity],
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

        # Avoid using exclude_none or any of those variants as
        # those are recursive, and leads to lossy component serialization.
        return file_data.model_dump_json(indent=2)

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
