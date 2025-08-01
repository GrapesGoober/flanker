from pydantic import BaseModel, create_model
from typing import Any, Optional


class Serializer:

    @staticmethod
    def serialize(entities: dict[int, dict[type, Any]], id_counter: int) -> str:
        # Extract unique component types
        component_types: list[type] = [
            comp_type for comps in entities.values() for comp_type in comps
        ]
        # Define file schema models using component fields
        component_fields: dict[str, Any] = {
            t.__name__: (Optional[t], None) for t in component_types
        }
        EntityComponent = create_model("EntityComponent", **component_fields)
        FileData = create_model(
            "FileData", id_counter=int, entities=dict[int, EntityComponent]
        )

        # Convert entities to using EntityComponent models
        typed_entities = {
            entity_id: EntityComponent(
                **{comp.__class__.__name__: comp for comp in comps.values()}
            )
            for entity_id, comps in entities.items()
        }

        # Serialize with nulls excluded
        return FileData(
            entities=typed_entities,
            id_counter=id_counter,
        ).model_dump_json(indent=2, exclude_none=True)

    @staticmethod
    def deserialize(
        json_data: str, component_types: list[type]
    ) -> tuple[int, dict[int, dict[type, Any]]]:

        # Define file schema models using component fields
        component_fields: dict[str, Any] = {
            t.__name__: (Optional[t], None) for t in component_types
        }
        EntityComponent = create_model("EntityComponent", **component_fields)
        FileData = create_model(
            "FileData", id_counter=int, entities=dict[int, EntityComponent]
        )

        # Serialize with nulls excluded
        file_data = FileData.model_validate_json(json_data)
        entities_data: dict[int, BaseModel] = getattr(file_data, "entities")
        id_counter: int = getattr(file_data, "id_counter")

        # Convert EntityComponent models to dict[type, Any] components
        entities: dict[int, dict[type, Any]] = {
            entity_id: {
                type(comp_obj): comp_obj
                for comp_name in EntityComponent.model_fields.keys()
                if (comp_obj := getattr(entity_components, comp_name)) is not None
            }
            for entity_id, entity_components in entities_data.items()
        }

        return id_counter, entities
