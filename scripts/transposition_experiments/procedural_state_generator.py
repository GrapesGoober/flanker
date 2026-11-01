import random
from copy import deepcopy

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
    for faction in [
        InitiativeState.Faction.BLUE,
        InitiativeState.Faction.BLUE,
        InitiativeState.Faction.RED,
        InitiativeState.Faction.RED,
    ]:
        gs.add_entity(
            MoveControls(),
            CombatUnit(
                faction=faction,
                status=CombatUnit.Status.ACTIVE,
            ),
            Transform(
                position=Vec2(
                    random.randint(10, 190),
                    random.randint(10, 190),
                ),
                degrees=0,
            ),
            FireControls(fov_degrees=None),
            AssaultControls(),
        )

    return gs
