import os
from dataclasses import dataclass
from typing import Iterable


@dataclass
class SceneEntry:
    path_sequence: list[str]
    name: str


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
                )


if __name__ == "__main__":
    print(list(get_scene_entries(directory_path="./scenes")))
