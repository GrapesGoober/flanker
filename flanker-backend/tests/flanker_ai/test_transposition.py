from copy import deepcopy
from dataclasses import dataclass, is_dataclass
from inspect import isclass
from typing import Any, Iterable, Literal
from uuid import UUID

import pytest
from flanker_ai.config_models import TranspositionScheme
from flanker_ai.search_states.common.ai_transposition_key_service import (
    AiTranspositionKeyService,
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
    unit_1_id: UUID
    unit_2_id: UUID
    transposition_schemes: list[TranspositionScheme.ALL]


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()

    unit_1_id = gs.add_entity(
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

    unit_2_id = gs.add_entity(
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
        unit_1_id=unit_1_id,
        unit_2_id=unit_2_id,
        transposition_schemes=[
            TranspositionScheme.RoundedPosition(
                type="RoundedPosition",
                to_nearest=33.33,
            ),
            TranspositionScheme.RoundedRotation(
                type="RoundedRotation",
                to_nearest=22.5,
            ),
            TranspositionScheme.LosSignatures(
                type="LosSignatures",
                with_fov=False,
            ),
            TranspositionScheme.LosSignatures(
                type="LosSignatures",
                with_fov=True,
            ),
        ],
    )


# TODO: remove this once test is over
def serialize_state(
    gs: GameState,
    name: str,
) -> None:

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

    with open(f"./scenes/local/{name}.json", "w") as f:
        f.write(serialize(gs, indent=2))


def test_same_state(fixture: Fixture) -> None:
    gs_1 = deepcopy(fixture.gs)
    gs_2 = deepcopy(fixture.gs)
    key_1 = AiTranspositionKeyService.get_key(
        gs=gs_1,
        transposition_schemes=fixture.transposition_schemes,
    )
    key_2 = AiTranspositionKeyService.get_key(
        gs=gs_2,
        transposition_schemes=fixture.transposition_schemes,
    )
    assert key_1 == key_2, "Two states must compare the same."


def test_different_unit(fixture: Fixture) -> None:
    gs_1 = deepcopy(fixture.gs)
    gs_2 = deepcopy(fixture.gs)
    unit_2 = gs_2.get_component(fixture.unit_2_id, CombatUnit)
    unit_2.status = CombatUnit.Status.PINNED

    key_1 = AiTranspositionKeyService.get_key(
        gs=gs_1,
        transposition_schemes=fixture.transposition_schemes,
    )
    key_2 = AiTranspositionKeyService.get_key(
        gs=gs_2,
        transposition_schemes=fixture.transposition_schemes,
    )
    assert key_1 != key_2, "The unit does not have same status."

    unit_2.status = CombatUnit.Status.ACTIVE
    key_2 = AiTranspositionKeyService.get_key(
        gs=gs_2,
        transposition_schemes=fixture.transposition_schemes,
    )
    assert key_1 == key_2, "The two states are the same."

    unit_2.faction = InitiativeState.Faction.RED
    key_2 = AiTranspositionKeyService.get_key(
        gs=gs_2,
        transposition_schemes=fixture.transposition_schemes,
    )
    assert key_1 != key_2, "The unit does not have same factions."


def test_position_rounding(fixture: Fixture) -> None:
    gs_1 = deepcopy(fixture.gs)
    gs_2 = deepcopy(fixture.gs)

    unit_2_transform = gs_2.get_component(fixture.unit_2_id, Transform)
    initial_position = unit_2_transform.position
    new_position = Vec2(65, 175)
    unit_2_transform.position = new_position

    key_1 = AiTranspositionKeyService.get_key(
        gs=gs_1,
        transposition_schemes=fixture.transposition_schemes,
    )
    key_2 = AiTranspositionKeyService.get_key(
        gs=gs_2,
        transposition_schemes=fixture.transposition_schemes,
    )
    assert (
        key_1 == key_2
    ), f"Position {initial_position} rounds to the same as {new_position}"

    new_position = Vec2(85, 175)
    unit_2_transform.position = new_position
    key_2 = AiTranspositionKeyService.get_key(
        gs=gs_2,
        transposition_schemes=fixture.transposition_schemes,
    )

    assert (
        key_1 != key_2
    ), f"Position {initial_position} is not the same as {new_position}"


def test_rotation_rounding(fixture: Fixture) -> None:
    gs_1 = deepcopy(fixture.gs)
    gs_2 = deepcopy(fixture.gs)

    unit_2_transform = gs_2.get_component(fixture.unit_2_id, Transform)
    initial_degrees = unit_2_transform.position
    new_degrees = -80
    unit_2_transform.degrees = new_degrees

    key_1 = AiTranspositionKeyService.get_key(
        gs=gs_1,
        transposition_schemes=fixture.transposition_schemes,
    )
    key_2 = AiTranspositionKeyService.get_key(
        gs=gs_2,
        transposition_schemes=fixture.transposition_schemes,
    )
    assert (
        key_1 == key_2
    ), f"Rotation {initial_degrees} rounds to the same as {new_degrees}"

    new_degrees = -45
    unit_2_transform.degrees = new_degrees
    key_2 = AiTranspositionKeyService.get_key(
        gs=gs_2,
        transposition_schemes=fixture.transposition_schemes,
    )

    assert (
        key_1 != key_2
    ), f"Rotation {initial_degrees} is not the same as {new_degrees}"
