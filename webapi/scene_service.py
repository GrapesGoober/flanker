from dataclasses import is_dataclass
from inspect import isclass
from pathlib import Path
from typing import Any, Iterable
from uuid import UUID

from flanker_ai.components import AiConfigComponent
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.models.components import (
    CombatUnit,
    FireControls,
    InitiativeState,
    Transform,
)
from flanker_core.serializer import Serializer
from flanker_core.systems.fire_system import FireSystem
from flanker_core.systems.initiative_system import InitiativeSystem
from flanker_core.systems.objective_system import ObjectiveSystem

from webapi.components import LogRecords, TerrainTypeTag
from webapi.models import GameViewState, GameViewStateResponse, SquadModel


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
    def get_scenes() -> list[str]:
        folder = Path("./scenes/")
        return [file.stem for file in folder.iterdir() if file.is_file()]

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

    @staticmethod
    def get_view_state(gs: GameState) -> GameViewState:
        """Get a view version of game state."""
        # Assume player faction is BLUE
        faction = InitiativeState.Faction.BLUE
        squads: list[SquadModel] = []
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
                    firing_at=fire_controls.firing_at,
                )
            )

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
        )

    @staticmethod
    def get_view_state_response(gs: GameState) -> GameViewStateResponse:
        return GameViewStateResponse(
            view_state=SceneService.get_view_state(gs),
            json_state=SceneService.serialize(gs),
        )
