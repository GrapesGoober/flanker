from dataclasses import dataclass
from uuid import UUID

import pytest
from flanker_core.gamestate import GameState
from flanker_core.models.actions import MoveAction, PivotAction
from flanker_core.models.components import (
    CombatUnit,
    InitiativeState,
    MoveControls,
    StallLoseCondition,
    TerrainFeature,
    Transform,
)
from flanker_core.models.vec2 import Vec2
from flanker_core.systems.action_system import ActionSystem
from flanker_core.systems.intersect_system import IntersectSystem
from flanker_core.systems.objective_system import ObjectiveSystem


@dataclass
class Fixture:
    gs: GameState
    unit_id_1: UUID
    unit_id_2: UUID


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    gs.add_entity(InitiativeState())
    # Rifle Squad
    unit_id_1 = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.BLUE),
        Transform(position=Vec2(0, -10)),
    )
    unit_id_2 = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=InitiativeState.Faction.BLUE),
        Transform(position=Vec2(5, -10)),
    )

    # Test the stall
    gs.add_entity(
        StallLoseCondition(
            counting_faction=InitiativeState.Faction.BLUE,
            winning_faction=InitiativeState.Faction.RED,
            stall_count=0,
            stall_limit=5,
        )
    )

    # 10x10 opaque box (not walkable)
    gs.add_entity(
        Transform(position=Vec2(0, 0), degrees=0),
        TerrainFeature(
            vertices=[
                Vec2(0, 0),
                Vec2(10, 0),
                Vec2(10, 10),
                Vec2(0, 10),
            ],
            flag=TerrainFeature.Flag.OPAQUE,
        ),
    )

    # 10x10 walkable box
    gs.add_entity(
        Transform(position=Vec2(0, 0), degrees=0),
        TerrainFeature(
            vertices=[
                Vec2(0, 0),
                Vec2(-10, 0),
                Vec2(-10, -10),
                Vec2(0, -10),
            ],
            flag=TerrainFeature.Flag.WALKABLE,
        ),
    )

    return Fixture(gs, unit_id_1, unit_id_2)


def test_terrain_intersects(fixture: Fixture) -> None:
    start, end = Vec2(-5, -6), Vec2(5, 4)
    intersects = IntersectSystem.get(
        gs=fixture.gs,
        start=start,
        end=end,
        mask=TerrainFeature.Flag.WALKABLE,
    )
    intersects = list(intersects)
    assert len(intersects) == 1, "There are 1 walkable terrains intersected"

    start, end = Vec2(-5, -6), Vec2(5, 4)
    intersects = IntersectSystem.get(
        gs=fixture.gs,
        start=start,
        end=end,
        mask=TerrainFeature.Flag.WALKABLE | TerrainFeature.Flag.OPAQUE,
    )
    intersects = list(intersects)
    assert len(intersects) == 2, "Both walkable and opaque are intersected"


def test_move(fixture: Fixture) -> None:
    ActionSystem.perform(fixture.gs, MoveAction(fixture.unit_id_1, Vec2(5, -15)))
    transform = fixture.gs.get_component(fixture.unit_id_1, Transform)
    assert transform.position == Vec2(5, -15), "Unit #1 expects at Vec2(5, -15)"
    assert transform.degrees == -45, "Unit #1 expects to pivot towards direction."
    ActionSystem.perform(fixture.gs, PivotAction(fixture.unit_id_1, Vec2(5, 100)))
    assert transform.position == Vec2(5, -15), "Pivot action shouldn't move unit"
    assert transform.degrees == 90, "Unit #1 expects to pivot towards direction."


def test_move_stall(fixture: Fixture) -> None:
    for _ in range(5):
        ActionSystem.perform(fixture.gs, MoveAction(fixture.unit_id_1, Vec2(5, -15)))
    winner = ObjectiveSystem.get_winning_faction(fixture.gs)
    assert winner == None, "Expects to be able to stall 5 times before losing."

    ActionSystem.perform(fixture.gs, MoveAction(fixture.unit_id_1, Vec2(5, -15)))
    winner = ObjectiveSystem.get_winning_faction(fixture.gs)
    assert winner == InitiativeState.Faction.RED, "Expects the 6th stall to lose."


def test_move_invalid(fixture: Fixture) -> None:
    ActionSystem.perform(fixture.gs, MoveAction(fixture.unit_id_1, Vec2(6, 6)))
    transform = fixture.gs.get_component(fixture.unit_id_1, Transform)
    assert transform.position == Vec2(0, -10), "Unit #1 expects to not move"
