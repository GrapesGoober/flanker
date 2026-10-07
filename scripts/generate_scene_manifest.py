from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from experiment_models import SceneManifest


@dataclass
class SceneEntry:
    path_sequence: list[str]
    path: str


def get_scene_entries(
    directory_path: Path,
    parent_names: list[str] = [],
) -> Iterable[SceneEntry]:

    for entry in directory_path.iterdir():
        name = entry.stem
        path_sequence: list[str] = parent_names + [name]
        if entry.is_dir():
            yield from get_scene_entries(
                directory_path=entry,
                parent_names=path_sequence,
            )
        elif entry.is_file():
            if entry.suffix != ".json":
                continue
            if name == "manifest":
                continue
            yield SceneEntry(
                path_sequence=path_sequence,
                path=str(entry),
            )


def get_scene_path_by_name(
    directory_path: Path,
) -> dict[str, str]:

    scene_path_by_name: dict[str, str] = {}
    for scene_entry in get_scene_entries(directory_path):
        name = "-".join(scene_entry.path_sequence)
        if name not in scene_path_by_name:
            scene_path_by_name[name] = scene_entry.path

    return scene_path_by_name


if __name__ == "__main__":

    manifest_path = Path("./scenes/manifest.json")
    with manifest_path.open("r") as f:
        manifest = SceneManifest.model_validate_json(f.read())

    manifest.scene_paths = get_scene_path_by_name(
        directory_path=Path("./scenes"),
    )

    with manifest_path.open("w") as f:
        f.write(manifest.model_dump_json(indent=2))
