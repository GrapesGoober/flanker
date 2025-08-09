from dataclasses import is_dataclass
from inspect import isclass
from typing import Any
from backend.tag_components import (
    TerrainTypeTag,
)
from core.gamestate import GameState
from core import components


class SceneService:

    @staticmethod
    def load_scene(path: str) -> GameState:
        component_types: list[type[Any]] = []
        for _, cls in vars(components).items():
            if isclass(cls) and is_dataclass(cls):
                component_types.append(cls)
        component_types.append(TerrainTypeTag)

        with open(path, "r") as f:
            gs = GameState.load(f.read(), component_types)

        return gs

    @staticmethod
    def save_scene(path: str, gs: GameState) -> None:
        with open(path, "w") as f:
            f.write(gs.save())
