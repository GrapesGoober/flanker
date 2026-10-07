from dataclasses import dataclass, is_dataclass
from inspect import isclass
from typing import Any, Iterable, Literal
from uuid import UUID

import pytest
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
    StallLoseCondition,
    TerrainFeature,
    Transform,
)
from flanker_core.models.outcomes import FireOutcomes
from flanker_core.models.vec2 import Vec2
from flanker_core.serializer import Serializer


@dataclass
class TerrainTypeTag:
    """Tag to store the terrain type."""

    type: Literal["FOREST"]


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
        Transform(position=Vec2(75, 25), degrees=90),
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
        Transform(position=Vec2(75, 175), degrees=-90),
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
                Vec2(50, 75),
                Vec2(50, 125),
                Vec2(100, 125),
                Vec2(100, 75),
            ],
            flag=TerrainFeature.Flag.OPAQUE,
        ),
        TerrainTypeTag(type="FOREST"),
    )

    gs.add_entity(
        MapBoundary(
            vertices=[
                Vec2(0, 0),
                Vec2(0, 200),
                Vec2(150, 200),
                Vec2(150, 0),
            ]
        ),
    )

    gs.add_entity(
        InitiativeState(
            faction=InitiativeState.Faction.BLUE,
        )
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


# TODO: remove this once test is over
def test_write(fixture: Fixture) -> None:

    def get_component_types() -> Iterable[type[Any]]:
        for _, cls in vars(components).items():
            if isclass(cls) and is_dataclass(cls):
                yield cls
        yield TerrainTypeTag

    def serialize(gs: GameState, indent: int | None = None) -> str:
        component_types = list(get_component_types())
        entities = gs.dump()
        return Serializer.serialize(
            entities,
            component_types,
            indent=indent,
        )

    with open("./scenes/local/test-transposition.json", "w") as f:
        f.write(serialize(fixture.gs, indent=2))
