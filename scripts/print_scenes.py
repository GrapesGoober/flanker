import os
from dataclasses import dataclass

from pydantic import TypeAdapter


@dataclass
class ScenesDirectory:
    entries: dict[str, "str | ScenesDirectory"]


def get_scenes_directory(
    root_path: str,
) -> ScenesDirectory:

    scenes = ScenesDirectory(entries={})
    with os.scandir(root_path) as entries:
        for entry in entries:
            if entry.is_dir():
                scenes.entries[entry.name] = get_scenes_directory(
                    root_path=entry.path,
                )
            elif entry.is_file():
                name, extension = os.path.splitext(entry.name)
                if extension != ".json":
                    continue
                scenes.entries[name] = entry.path
    return scenes


if __name__ == "__main__":
    scenes = get_scenes_directory(root_path="./scenes")
    print(TypeAdapter(ScenesDirectory).dump_json(scenes, indent=2).decode())
