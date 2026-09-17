from dataclasses import is_dataclass
from inspect import isclass
from pathlib import Path
from typing import Any, FrozenSet, Iterable
from uuid import UUID

from flanker_ai.ai_agent import AiAgent
from flanker_ai.components import AiConfigComponent
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.models.actions import MoveAction
from flanker_core.models.components import (
    CombatUnit,
    FireControls,
    InitiativeState,
    Transform,
)
from flanker_core.models.vec2 import Vec2
from flanker_core.serializer import Serializer
from flanker_core.systems.fire_system import FireSystem
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.los_system import LosSystem
from flanker_core.systems.objective_system import ObjectiveSystem
from flanker_core.utils.polygon_utils import PolygonUtils
from webapi.components import LogRecords, TerrainTypeTag
from webapi.models import (
    FireEffectPair,
    GameStateInspection,
    GameViewState,
    GameViewStateResponse,
    SceneManifest,
    SceneManifestResponse,
    SquadModel,
)


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
            else SceneManifest(quick_access={}, scene_paths={})
        )

        # Combine both. Local takes priority (right hand side)
        return SceneManifest(
            quick_access=manifest.quick_access | local_manifest.quick_access,
            scene_paths=manifest.scene_paths | local_manifest.scene_paths,
        )

    @staticmethod
    def get_scenes() -> SceneManifestResponse:
        manifest = SceneService.get_manifest()

        return SceneManifestResponse(
            quick_access_scenes=list(manifest.quick_access.keys()),
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

    @staticmethod
    def load_from_quick_access(
        quick_access_name: str,
    ) -> GameState:
        with open("./scenes/manifest.json", "r") as f:
            manifest = SceneManifest.model_validate_json(f.read())
        scene_names = manifest.quick_access[quick_access_name]
        return SceneService.load_game_state(scene_names)

    @staticmethod
    def get_view_state(gs: GameState) -> GameViewState:
        """Get a view version of game state."""
        # Assume player faction is BLUE
        faction = InitiativeState.Faction.BLUE

        # Grab all the squads and build its view models
        squads: list[SquadModel] = []
        fire_effect_pairs: dict[FrozenSet[UUID], FireEffectPair] = {}
        for unit_id, unit, transform, fire_controls in gs.query(
            CombatUnit,
            Transform,
            FireControls,
        ):
            squads.append(
                SquadModel(
                    unit_id=unit_id,
                    position=transform.position,
                    degree=transform.degrees,
                    status=FireSystem.get_status(gs, unit_id),
                    is_friendly=(unit.faction == faction),
                    fov_degrees=fire_controls.fov_degrees,
                    firing_at=fire_controls.firing_at,
                )
            )

            if fire_controls.firing_at != None:
                target_id, fire_effect = fire_controls.firing_at
                fire_effect_key = frozenset((unit_id, target_id))
                if fire_effect_key in fire_effect_pairs:
                    fire_effect_pairs[fire_effect_key].fire_effect_b = fire_effect
                else:
                    target_transform = gs.get_component(target_id, Transform)
                    fire_effect_pairs[fire_effect_key] = FireEffectPair(
                        position_a=transform.position,
                        position_b=target_transform.position,
                        fire_effect_a=fire_effect,
                        fire_effect_b=None,
                    )

        # Grab all the game match data
        has_initiative = InitiativeSystem.get_initiative(gs) == faction
        winning_faction = ObjectiveSystem.get_winning_faction(gs)
        if winning_faction == faction:
            objective_state = GameViewState.ObjectiveState.COMPLETED
        elif winning_faction == None:
            objective_state = GameViewState.ObjectiveState.INCOMPLETE
        else:
            objective_state = GameViewState.ObjectiveState.FAILED

        return GameViewState(
            objective_state=objective_state,
            has_initiative=has_initiative,
            squads=squads,
            fire_effect_pairs=list(fire_effect_pairs.values()),
        )

    @staticmethod
    def get_view_state_response(gs: GameState) -> GameViewStateResponse:
        return GameViewStateResponse(
            view_state=SceneService.get_view_state(gs),
            json_state=SceneService.serialize(gs),
        )

    @staticmethod
    def get_inspection(gs: GameState) -> GameStateInspection:
        los_polygons: list[GameStateInspection.LosPolygon] = []
        for _, unit, transform, fire_controls in gs.query(
            CombatUnit, Transform, FireControls
        ):
            los_polygon = LosSystem.get_los_polygon(
                gs,
                spotter_pos=transform.position,
            )

            if fire_controls.fov_degrees != None:
                fov_polygon = PolygonUtils.clip_by_fov_cone(
                    polyline=los_polygon,
                    center_point=transform.position,
                    heading_degree=transform.degrees,
                    fov_degrees=fire_controls.fov_degrees,
                )
            else:
                fov_polygon = los_polygon

            los_polygons.append(
                GameStateInspection.LosPolygon(
                    faction=unit.faction,
                    los_polygon=los_polygon,
                    fov_polygon=fov_polygon,
                )
            )

        agent = AiAgent.get_agent(gs, InitiativeState.Faction.BLUE)
        agent.rs.update_state(gs)
        actions = [a for a in agent.rs.get_actions() if isinstance(a, MoveAction)]
        unit_id = actions[0].unit_id if actions else None
        move_candidates: list[Vec2] = [a.to for a in actions if a.unit_id == unit_id]

        return GameStateInspection(
            view_state=SceneService.get_view_state(gs),
            los_polygons=los_polygons,
            move_candidates=move_candidates,
        )
