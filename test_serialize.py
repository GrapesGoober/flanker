from dataclasses import is_dataclass
import inspect
from typing import Any
from backend.terrain_controller import TerrainController
from core.gamestate import GameState
from core import components

manifest: list[type[Any]] = []
for name, cls in vars(components).items():
    if inspect.isclass(cls) and is_dataclass(cls):
        manifest.append(cls)

manifest.append(TerrainController.TypeTag)

# from backend.scene import new_scene
# context = new_scene()
# json_str = context.gs.save()
# print(json_str)

with open("entities.json", "r") as f:
    gs = GameState.load(f.read(), manifest)

with open("entities.json", "w") as f:
    f.write(gs.save())
