from dataclasses import is_dataclass
from inspect import isclass
from pathlib import Path
from typing import Any, Iterable
from uuid import UUID

from flanker_ai.config_models import AiConfigComponent
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.serializer import Serializer
from webapi.components import LogRecords, TerrainTypeTag
from webapi.models import SceneManifest, SceneManifestResponse


class SceneService:

    @staticmethod
    def _get_component_types() -> Iterable[type[Any]]:
        for _, cls in vars(components).items():
            if isclass(cls) and is_dataclass(cls):
                yield cls
        yield TerrainTypeTag
        yield AiConfigComponent
        yield LogRecords

    @staticmethod
    def get_manifest() -> SceneManifest:

        # Load the default manifest. Throw if not exists.
        manifest = SceneManifest.model_validate_json(
            Path("./scenes/manifest.json").read_text()
        )

        # Load the local manifest. This is optional
        local_manifest_path = Path("./scenes/local/manifest.json")
        local_manifest = (
            SceneManifest.model_validate_json(local_manifest_path.read_text())
            if local_manifest_path.exists()
            else SceneManifest(scene_paths={})
        )

        # Combine both. Local takes priority (right hand side)
        return SceneManifest(
            scene_paths=manifest.scene_paths | local_manifest.scene_paths,
        )

    @staticmethod
    def get_scenes() -> SceneManifestResponse:
        manifest = SceneService.get_manifest()

        return SceneManifestResponse(
            scene_names=list(manifest.scene_paths.keys()),
        )

    @staticmethod
    def serialize(gs: GameState, indent: int | None = None) -> str:
        component_types = list(SceneService._get_component_types())
        entities = gs.dump()
        return Serializer.serialize(
            entities,
            component_types,
            indent=indent,
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

        manifest = SceneService.get_manifest()
        paths = [manifest.scene_paths[name] for name in scene_names]

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
