import random
from copy import deepcopy
from math import ceil, floor

from flanker_core.gamestate import GameState
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
    TerrainFeature,
    Transform,
)
from flanker_core.models.vec2 import Vec2
from flanker_core.utils.polygon_utils import PolygonUtils


def get_map() -> GameState:
    """
    Generates an empty state containing just the terrains and boundary.
    """
    # TODO: need PCG for this step. Using a hand-drawn scene for now.
    gs = GameState()
    gs.add_entity(
        MapBoundary(
            vertices=[
                Vec2(0, 0),
                Vec2(200, 0),
                Vec2(200, 200),
                Vec2(0, 200),
            ]
        )
    )
    gs.add_entity(
        TerrainFeature(
            vertices=[
                Vec2(75, 75),
                Vec2(125, 75),
                Vec2(125, 125),
                Vec2(75, 125),
            ],
            flag=TerrainFeature.Flag.OPAQUE | TerrainFeature.Flag.WALKABLE,
        )
    )
    return gs


def get_state_from_map(
    map: GameState,
) -> GameState:
    gs = deepcopy(map)
    """
    Given the empty map state, populate with combat units and other entities.
    This makes it a complete state that is game-tree runnable. 
    """

    # TODO: have it randomize initial faction
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
    max_x = floor(max(vertex.x for vertex in boundary))
    min_y = ceil(min(vertex.y for vertex in boundary))
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
                random.randint(min_x, max_x),
                random.randint(min_y, max_y),
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
