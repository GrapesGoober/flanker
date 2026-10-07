import json
import os
from dataclasses import dataclass
from typing import Iterable


@dataclass
class SceneEntry:
    path_sequence: list[str]
    name: str
    path: str


def get_scene_entries(
    directory_path: str,
    parent_names: list[str] = [],
) -> Iterable[SceneEntry]:

    with os.scandir(directory_path) as entries:
        for entry in entries:
            name, extension = os.path.splitext(entry.name)
            path_sequence: list[str] = parent_names + [name]
            if entry.is_dir():
                yield from get_scene_entries(
                    directory_path=entry.path,
                    parent_names=path_sequence,
                )
            elif entry.is_file():
                if extension != ".json":
                    continue
                yield SceneEntry(
                    path_sequence=path_sequence,
                    name=name,
                    path=entry.path,
                )


def get_scene_path_by_name(
    directory_path: str = "./scenes",
) -> dict[str, str]:

    scene_path_by_name: dict[str, str] = {}
    for scene_entry in get_scene_entries(directory_path):
        name = scene_entry.name
        if name not in scene_path_by_name:
            scene_path_by_name[name] = scene_entry.path

    return scene_path_by_name


if __name__ == "__main__":
    print(
        json.dumps(
            get_scene_path_by_name(directory_path=".\\scenes"),
            indent=2,
        )
    )
