from dataclasses import is_dataclass
from inspect import isclass
from typing import Any, Iterable
from uuid import UUID

from flanker_ai.components import AiConfigComponent
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.serializer import Serializer

from webapi.tag_components import TerrainTypeTag


class SceneService:

    def __init__(self) -> None:
        self.games: dict[str, dict[int, GameState]] = {}

    @staticmethod
    def _get_component_types() -> Iterable[type[Any]]:
        for _, cls in vars(components).items():
            if isclass(cls) and is_dataclass(cls):
                yield cls
        yield TerrainTypeTag
        yield AiConfigComponent

    def save_scene(
        self,
        scene_name: str,
        game_id: int,
        path: str,
    ) -> None:
        gs = self.get_game_state(scene_name, game_id)
        component_types = list(SceneService._get_component_types())
        with open(path, "w") as f:
            entities = gs.dump()
            f.write(
                Serializer.serialize(
                    entities,
                    component_types,
                )
            )

    def get_game_state(
        self,
        scene_name: str,
        game_id: int,
    ) -> GameState:
        # Initialize a new set of games for a scene
        games = self.games.setdefault(scene_name, {})
        # Initializing a new game is costly (file read),
        # So only initialize if not exists
        if game_id not in games:
            path = f"./scenes/{scene_name}.json"
            gs = SceneService.load_game_state([path])
            self.games[scene_name].setdefault(game_id, gs)
        return self.games[scene_name][game_id]

    def set_new_game_state(
        self,
        scene_names: list[str],
        scene_key: str,
        game_id: int,
    ) -> GameState:
        paths = [f"./scenes/{name}.json" for name in scene_names]
        gs = SceneService.load_game_state(paths)
        self.games.setdefault(scene_key, {})
        self.games[scene_key][game_id] = gs
        return gs

    @staticmethod
    def load_game_state(
        paths: list[str],
    ) -> GameState:
        component_types = list(SceneService._get_component_types())
        entities: dict[UUID, Any] = {}
        for path in paths:
            with open(path, "r") as f:
                entities.update(
                    Serializer.deserialize(
                        json_data=f.read(),
                        component_types=component_types,
                    )
                )

        gs = GameState.load(entities)
        return gs
