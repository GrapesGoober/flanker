import json
import os

type ScenesDirectory = dict[str, "str | ScenesDirectory"]


def get_scenes_directory(
    root_path: str,
) -> ScenesDirectory:

    scenes: ScenesDirectory = {}
    with os.scandir(root_path) as entries:
        for entry in entries:
            if entry.is_dir():
                scenes[entry.name] = get_scenes_directory(
                    root_path=entry.path,
                )
            elif entry.is_file():
                name, extension = os.path.splitext(entry.name)
                if extension != ".json":
                    continue
                scenes[name] = entry.path
    return scenes


if __name__ == "__main__":
    scenes = get_scenes_directory(root_path="./scenes")
    print(json.dumps(scenes, indent=2))
