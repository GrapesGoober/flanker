from dataclasses import dataclass
import pytest

from core.components import FactionManager, MoveControls, TerrainFeature, CombatUnit
from core.gamestate import GameState
from core.los_system import Transform
from core.move_system import MoveSystem
from core.utils.vec2 import Vec2


@dataclass
class Fixture:
    gs: GameState
    unit_id: int


@pytest.fixture
def fixture() -> Fixture:
    gs = GameState()
    gs.add_entity(FactionManager())
    # Rifle Squad
    id = gs.add_entity(
        MoveControls(),
        CombatUnit(faction=FactionManager.FactionType.FACTION_A),
        Transform(position=Vec2(0, -10)),
    )
    # 10x10 opaque box
    gs.add_entity(
        Transform(position=Vec2(0, 0), degrees=0),
        TerrainFeature(
            vertices=[
                Vec2(0, 0),
                Vec2(10, 0),
                Vec2(10, 10),
                Vec2(0, 10),
                Vec2(0, 0),
            ],
            flag=TerrainFeature.Flag.OPAQUE,
        ),
    )

    # 10x10 opaque box
    gs.add_entity(
        Transform(position=Vec2(0, 0), degrees=0),
        TerrainFeature(
            vertices=[
                Vec2(0, 0),
                Vec2(-10, 0),
                Vec2(-10, -10),
                Vec2(0, -10),
                Vec2(0, 0),
            ],
            flag=TerrainFeature.Flag.WALKABLE,
        ),
    )

    return Fixture(gs, id)


def test_move(fixture: Fixture) -> None:
    MoveSystem.move(fixture.gs, fixture.unit_id, Vec2(5, -15))
    transform = fixture.gs.get_component(fixture.unit_id, Transform)
    assert transform.position == Vec2(5, -15), "Unit expects at Vec2(5, -15)"


def test_move_invalid(fixture: Fixture) -> None:
    MoveSystem.move(fixture.gs, fixture.unit_id, Vec2(6, 6))
    transform = fixture.gs.get_component(fixture.unit_id, Transform)
    assert transform.position == Vec2(0, -10), "Unit expects to not move"
