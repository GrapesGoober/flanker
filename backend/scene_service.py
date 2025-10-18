from dataclasses import is_dataclass
from inspect import isclass
from typing import Any, Iterable
from backend.tag_components import (
    TerrainTypeTag,
)
from core.gamestate import GameState
from core import components


class SceneService:

    def __init__(self) -> None:
        self.games: dict[str, list[GameState]] = {}

    @staticmethod
    def _get_component_types() -> Iterable[type[Any]]:
        for _, cls in vars(components).items():
            if isclass(cls) and is_dataclass(cls):
                yield cls
        yield TerrainTypeTag

    @staticmethod
    def load_scene(path: str) -> GameState:
        component_types = list(SceneService._get_component_types())
        with open(path, "r") as f:
            gs = GameState.load(f.read(), component_types)

        return gs

    @staticmethod
    def save_scene(path: str, gs: GameState) -> None:
        component_types = list(SceneService._get_component_types())
        with open(path, "w") as f:
            f.write(gs.save(component_types))

    def get_game_state(self, scene_name: str, game_id: int) -> GameState:
        if scene_name not in self.games or game_id >= len(self.games[scene_name]):
            self.games.setdefault(scene_name, []).append(
                SceneService.load_scene(f"./scenes/{scene_name}.json")
            )
        return self.games[scene_name][game_id]
