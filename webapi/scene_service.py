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

    @staticmethod
    def _get_component_types() -> Iterable[type[Any]]:
        for _, cls in vars(components).items():
            if isclass(cls) and is_dataclass(cls):
                yield cls
        yield TerrainTypeTag
        yield AiConfigComponent

    @staticmethod
    def serialize(gs: GameState) -> str:
        component_types = list(SceneService._get_component_types())
        entities = gs.dump()
        return Serializer.serialize(
            entities,
            component_types,
        )

    @staticmethod
    def deserialize(serialized_gs: str) -> GameState:
        component_types = list(SceneService._get_component_types())
        entities = Serializer.deserialize(serialized_gs, component_types)
        return GameState.load(entities)

    @staticmethod
    def load_game_state(
        scene_names: list[str],
    ) -> GameState:
        component_types = list(SceneService._get_component_types())
        entities: dict[UUID, Any] = {}
        for scene in scene_names:
            path = f"./scenes/{scene}.json"
            with open(path, "r") as f:
                entities.update(
                    Serializer.deserialize(
                        json_data=f.read(),
                        component_types=component_types,
                    )
                )

        gs = GameState.load(entities)
        return gs
