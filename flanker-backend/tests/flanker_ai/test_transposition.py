from dataclasses import dataclass
from uuid import UUID

import pytest
from flanker_core.gamestate import GameState
from flanker_core.models.components import (
    AssaultControls,
    CombatUnit,
    EliminationWinCondition,
    FireControls,
    InitiativeState,
    MapBoundary,
    MoveControls,
    StallLoseCondition,
    TerrainFeature,
    Transform,
)
from flanker_core.models.outcomes import FireOutcomes
from flanker_core.models.vec2 import Vec2


@dataclass
class Fixture:
    gs: GameState
    friendly_id: UUID
    enemy_id: UUID


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()

    friendly_id = gs.add_entity(
        MoveControls(),
        CombatUnit(
            faction=InitiativeState.Faction.BLUE,
            status=CombatUnit.Status.ACTIVE,
        ),
        Transform(position=Vec2(15, 5), degrees=-90),
        FireControls(
            fov_degrees=90,
            override=FireOutcomes.PIN,
        ),
        AssaultControls(),
    )

    enemy_id = gs.add_entity(
        MoveControls(),
        CombatUnit(
            faction=InitiativeState.Faction.BLUE,
            status=CombatUnit.Status.ACTIVE,
        ),
        Transform(position=Vec2(15, 25), degrees=90),
        FireControls(
            fov_degrees=90,
            override=FireOutcomes.PIN,
        ),
        AssaultControls(),
    )

    gs.add_entity(
        Transform(
            position=Vec2(0, 0),
            degrees=0,
        ),
        TerrainFeature(
            vertices=[
                Vec2(10, 15),
                Vec2(10, 25),
                Vec2(20, 25),
                Vec2(20, 15),
            ]
        ),
    )

    gs.add_entity(
        MapBoundary(
            vertices=[
                Vec2(0, 0),
                Vec2(0, 50),
                Vec2(30, 50),
                Vec2(30, 0),
            ]
        ),
    )

    gs.add_entity(
        EliminationWinCondition(
            target_faction=InitiativeState.Faction.RED,
            winning_faction=InitiativeState.Faction.BLUE,
            units_to_eliminate=1,
            units_eliminated_counter=0,
        )
    )
    gs.add_entity(
        EliminationWinCondition(
            target_faction=InitiativeState.Faction.BLUE,
            winning_faction=InitiativeState.Faction.RED,
            units_to_eliminate=1,
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

    return Fixture(
        gs=gs,
        friendly_id=friendly_id,
        enemy_id=enemy_id,
    )
