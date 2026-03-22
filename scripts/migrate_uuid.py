import json
import uuid
from typing import Any


def migrate_to_uuid(input_path: str, output_path: str) -> None:
    with open(input_path, "r", encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)

    old_entities: dict[str, Any] = data.get("entities", {})

    # Map old int IDs → new UUID strings
    id_map: dict[str, str] = {}

    for old_id in old_entities.keys():
        id_map[old_id] = str(uuid.uuid4())

    # Rebuild entities with UUID keys
    new_entities: dict[str, Any] = {}
    for old_id, entity in old_entities.items():
        new_id = id_map[old_id]
        new_entities[new_id] = entity

    # Build new data (remove id_counter)
    new_data = {"entities": new_entities}

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2)


if __name__ == "__main__":
    SCENE_NAME = "experiment-template"
    path = f"./scenes/{SCENE_NAME}.json"
    migrate_to_uuid(path, path)
