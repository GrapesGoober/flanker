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
        self.games: dict[str, dict[int, GameState]] = {}

    @staticmethod
    def _get_component_types() -> Iterable[type[Any]]:
        for _, cls in vars(components).items():
            if isclass(cls) and is_dataclass(cls):
                yield cls
        yield TerrainTypeTag

    def save_scene(self, scene_name: str, game_id: int, path: str) -> None:
        gs = self.get_game_state(scene_name, game_id)
        component_types = list(SceneService._get_component_types())
        with open(path, "w") as f:
            f.write(gs.save(component_types))

    def get_game_state(self, scene_name: str, game_id: int) -> GameState:
        # Initialize a new set of games for a scene
        games = self.games.setdefault(scene_name, {})
        # Initializing a new game is costly (file read),
        # So only initialize if not exists
        if game_id not in games:
            component_types = list(SceneService._get_component_types())
            with open(f"./scenes/{scene_name}.json", "r") as f:
                gs = GameState.load(f.read(), component_types)
            self.games[scene_name].setdefault(game_id, gs)
        return self.games[scene_name][game_id]
