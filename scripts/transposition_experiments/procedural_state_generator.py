import random
from copy import deepcopy
from dataclasses import is_dataclass
from inspect import isclass
from math import ceil, floor
from typing import Any
from uuid import UUID

from flanker_ai.config_models import (
    AiConfigComponent,
    PointsConfig,
    PolicyConfig,
    SearchPolicyConfig,
    TranspositionScheme,
    UnabstractedStateConfig,
)
from flanker_core.gamestate import GameState
from flanker_core.models import components
from flanker_core.models.components import (
    AssaultControls,
    CombatUnit,
    EliminationWinCondition,
    FireControls,
    InitiativeState,
    MapBoundary,
    MoveControls,
    RallyStallLoseCondition,
    StallLoseCondition,
    Transform,
)
from flanker_core.models.vec2 import Vec2
from flanker_core.serializer import Serializer
from flanker_core.utils.polygon_utils import PolygonUtils
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class SceneManifest(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    scene_paths: dict[str, str]


def get_game_state(
    scene_names: list[str],
) -> GameState:
    component_types = [
        component
        for _, component in vars(components).items()
        if isclass(component) and is_dataclass(component)
    ]
    entities: dict[UUID, Any] = {}

    with open("./scenes/manifest.json", "r") as f:
        manifest = SceneManifest.model_validate_json(f.read())

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


def get_map() -> GameState:
    """
    Generates an empty state containing just the terrains and boundary.
    """
    # TODO: need PCG for this step. Using a hand-drawn scene for now.
    return get_game_state(["scene-v2-1-no-units"])


def get_state_from_map(
    map: GameState,
) -> GameState:
    """
    Given the empty map state, populate with combat units and configs.
    This makes it a complete state that is game-tree runnable.
    """
    gs = deepcopy(map)

    add_ai_configs(gs)

    # TODO: have it randomize initial initiative
    gs.add_entity(
        InitiativeState(
            faction=InitiativeState.Faction.BLUE,
        )
    )
    gs.add_entity(
        EliminationWinCondition(
            target_faction=InitiativeState.Faction.RED,
            winning_faction=InitiativeState.Faction.BLUE,
            units_to_eliminate=2,
            units_eliminated_counter=0,
        )
    )
    gs.add_entity(
        EliminationWinCondition(
            target_faction=InitiativeState.Faction.BLUE,
            winning_faction=InitiativeState.Faction.RED,
            units_to_eliminate=2,
            units_eliminated_counter=0,
        )
    )
    gs.add_entity(
        StallLoseCondition(
            counting_faction=InitiativeState.Faction.BLUE,
            winning_faction=InitiativeState.Faction.RED,
            stall_count=0,
            stall_limit=5,
        )
    )
    gs.add_entity(
        StallLoseCondition(
            counting_faction=InitiativeState.Faction.RED,
            winning_faction=InitiativeState.Faction.BLUE,
            stall_count=0,
            stall_limit=5,
        )
    )
    gs.add_entity(
        RallyStallLoseCondition(
            rally_stall_count=0,
            rally_stall_limit=2,
            last_rallied_faction=None,
        ),
    )

    # Generates 2 blue and 2 red units at random positions.
    # TODO: remove the hardcoding, and make it generates more cases.

    boundary = []
    for _, map_boundary in gs.query(MapBoundary):
        boundary = map_boundary.vertices
        break
    if not boundary:
        raise RuntimeError("Map boundary not found.")

    min_x = ceil(min(vertex.x for vertex in boundary))
    min_y = ceil(min(vertex.y for vertex in boundary))
    max_x = floor(max(vertex.x for vertex in boundary))
    max_y = floor(max(vertex.y for vertex in boundary))
    if min_x > max_x or min_y > max_y:
        raise ValueError("Map boundary contains no integer coordinates.")

    for faction in [
        InitiativeState.Faction.BLUE,
        InitiativeState.Faction.BLUE,
        InitiativeState.Faction.RED,
        InitiativeState.Faction.RED,
    ]:
        position: Vec2 | None = None
        while position is None or not is_point_in_bound(gs, position):
            position = Vec2(
                # Don't let it touch the walls.
                random.randint(min_x + 10, max_x - 10),
                random.randint(min_y + 10, max_y - 10),
            )

        gs.add_entity(
            MoveControls(),
            CombatUnit(
                faction=faction,
                status=CombatUnit.Status.ACTIVE,
            ),
            Transform(
                position=position,
                degrees=0,
            ),
            FireControls(fov_degrees=None),
            AssaultControls(),
        )

    return gs


def add_ai_configs(gs: GameState) -> None:

    config = SearchPolicyConfig(
        policy=PolicyConfig.MinimaxPolicy(
            type="MinimaxPolicy",
            depth=4,
        ),
        state=UnabstractedStateConfig(
            type="UnabstractedStateConfig",
            move_candidates_pool=PointsConfig.Grid(
                type="GridConfig",
                spacing=50,
                offset=25,
            ),
            move_candidates_filter=[],
            transposition_schemes=[
                TranspositionScheme.RoundedPosition(
                    type="RoundedPosition",
                    to_nearest=1,
                ),
            ],
        ),
    )
    gs.add_entity(
        AiConfigComponent(
            faction=InitiativeState.Faction.BLUE,
            config=config,
        ),
    )
    gs.add_entity(
        AiConfigComponent(
            faction=InitiativeState.Faction.RED,
            config=config,
        ),
    )


def is_point_in_bound(
    gs: GameState,
    point: Vec2,
) -> bool:
    bound = []
    for _, map_boundary in gs.query(MapBoundary):
        bound = map_boundary.vertices
        break
    if not bound:
        raise RuntimeError("Map boundary not found.")
    if bound[-1] != bound[0]:
        bound = [*bound, bound[0]]
    return PolygonUtils.is_inside(point, bound)


def get_perturbed_state(
    gs: GameState,
) -> GameState:
    gs = deepcopy(gs)
    for _, _, transform in gs.query(CombatUnit, Transform):
        position: Vec2 | None = None
        while position is None or not is_point_in_bound(gs, position):
            position = Vec2(
                transform.position.x + random.randrange(-10, 10),
                transform.position.y + random.randrange(-10, 10),
            )
        transform.position = position
    return gs
